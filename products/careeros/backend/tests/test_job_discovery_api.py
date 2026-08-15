"""
Integration tests for job discovery via the real API. Uses a fake
JobProviderClient (deterministic, in-process) injected via
dependency_overrides -- never the real network, per this project's
established pattern (see test_document_intelligence_api.py's Mock
provider override).
"""
import pytest

from app.api.deps import get_job_provider
from app.job_discovery.provider import JobProviderFetchError, RawJobListing
from app.main import app

pytestmark = pytest.mark.asyncio


class FakeJobProviderClient:
    provider_name = "fake-provider"

    def __init__(self, listings=None, fail=False):
        self._listings = listings if listings is not None else _DEFAULT_LISTINGS
        self._fail = fail

    async def search(self, query, location, remote_only):
        if self._fail:
            raise JobProviderFetchError("simulated provider failure")
        return self._listings

    async def health_check(self):
        return not self._fail


_DEFAULT_LISTINGS = [
    RawJobListing(
        external_id="job-1",
        title="Systems Engineer",
        company_name="Test Corp",
        location="Birmingham",
        is_remote=False,
        salary_min=45000,
        salary_max=60000,
        salary_currency="GBP",
        salary_disclosed=True,
        description="A systems engineering role.",
        source_url="https://example.com/job-1",
        posted_at=None,
    ),
    RawJobListing(
        external_id="job-2",
        title="Cloud Engineer (Remote)",
        company_name="Remote Test Co",
        location="UK Remote",
        is_remote=True,
        salary_min=None,
        salary_max=None,
        salary_currency=None,
        salary_disclosed=False,
        description="A remote cloud role.",
        source_url="https://example.com/job-2",
        posted_at=None,
    ),
]


@pytest.fixture(autouse=True)
def _override_provider():
    app.dependency_overrides[get_job_provider] = lambda: FakeJobProviderClient()
    yield
    app.dependency_overrides.pop(get_job_provider, None)


async def _person_headers(client, email="jobdiscovery@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret1", "full_name": "Test Person"},
    )
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret1"})
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    await client.post(
        "/api/v1/career-dna/person", json={"first_name": "Test", "last_name": "Person"}, headers=headers
    )
    return headers


class TestDiscoveryEndpoint:
    async def test_discover_requires_auth(self, client):
        resp = await client.post("/api/v1/job-discovery/discover", json={})
        assert resp.status_code == 401

    async def test_discover_persists_new_listings(self, client):
        headers = await _person_headers(client)
        resp = await client.post("/api/v1/job-discovery/discover", json={}, headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["listings_found"] == 2
        assert body["listings_new"] == 2
        assert body["listings_duplicate"] == 0
        assert body["provider_name"] == "fake-provider"

    async def test_discover_derives_query_from_latest_employment(self, client):
        headers = await _person_headers(client)
        await client.post(
            "/api/v1/career-dna/employments",
            json={
                "employer_name": "Acme Corp",
                "role_title": "Senior Systems Engineer",
                "employment_type": "full_time",
                "start_date": "2022-01-01",
                "is_current": True,
            },
            headers=headers,
        )
        resp = await client.post("/api/v1/job-discovery/discover", json={}, headers=headers)
        assert resp.json()["query_used"] == "Senior Systems Engineer"

    async def test_discover_falls_back_to_skills_when_no_employment(self, client):
        headers = await _person_headers(client)
        await client.post(
            "/api/v1/career-dna/person-skills",
            json={"skill_name": "Kubernetes", "skill_type": "technical", "proficiency": "advanced"},
            headers=headers,
        )
        resp = await client.post("/api/v1/job-discovery/discover", json={}, headers=headers)
        assert "Kubernetes" in resp.json()["query_used"]

    async def test_discover_running_twice_deduplicates(self, client):
        headers = await _person_headers(client)
        first = await client.post("/api/v1/job-discovery/discover", json={}, headers=headers)
        second = await client.post("/api/v1/job-discovery/discover", json={}, headers=headers)
        assert first.json()["listings_new"] == 2
        assert second.json()["listings_new"] == 0
        assert second.json()["listings_duplicate"] == 2

    async def test_discover_accepts_overrides(self, client):
        headers = await _person_headers(client)
        resp = await client.post(
            "/api/v1/job-discovery/discover",
            json={"location": "London", "remote_only": True, "salary_min": 50000, "salary_max": 90000},
            headers=headers,
        )
        assert resp.status_code == 200  # override values accepted; the fake provider ignores them by design

    async def test_provider_failure_returns_clean_502_not_500(self, client):
        headers = await _person_headers(client)
        app.dependency_overrides[get_job_provider] = lambda: FakeJobProviderClient(fail=True)
        resp = await client.post("/api/v1/job-discovery/discover", json={}, headers=headers)
        assert resp.status_code == 502
        assert "error" in resp.json()

    async def test_empty_result_set_handled_cleanly(self, client):
        headers = await _person_headers(client)
        app.dependency_overrides[get_job_provider] = lambda: FakeJobProviderClient(listings=[])
        resp = await client.post("/api/v1/job-discovery/discover", json={}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["listings_found"] == 0


class TestListingsEndpoint:
    async def test_posted_at_flows_through_full_pipeline(self, client):
        """Section 1 remediation regression test: a real provider
        timestamp (RawJobListing.posted_at, already an ISO string as
        the provider layer produces) must survive discovery_service's
        persistence and be visible in the API response -- confirms all
        three layers (provider -> service -> schema) that needed fixing
        are actually wired together, not just individually correct."""
        headers = await _person_headers(client)
        app.dependency_overrides[get_job_provider] = lambda: FakeJobProviderClient(
            listings=[
                RawJobListing(
                    external_id="job-with-date",
                    title="Dated Role",
                    company_name="Dated Corp",
                    location="Birmingham",
                    is_remote=False,
                    salary_min=None,
                    salary_max=None,
                    salary_currency=None,
                    salary_disclosed=False,
                    description="A role with a real posted date.",
                    source_url="https://example.com/job-with-date",
                    posted_at="2026-08-14T21:30:28+00:00",
                )
            ]
        )
        await client.post("/api/v1/job-discovery/discover", json={}, headers=headers)
        resp = await client.get("/api/v1/job-discovery/listings", headers=headers)
        listing = resp.json()["items"][0]
        assert listing["posted_at"] is not None
        assert listing["posted_at"].startswith("2026-08-14T21:30:28")

    async def test_missing_posted_at_stays_null_not_invented(self, client):
        headers = await _person_headers(client)
        await client.post("/api/v1/job-discovery/discover", json={}, headers=headers)
        resp = await client.get("/api/v1/job-discovery/listings", headers=headers)
        # _DEFAULT_LISTINGS has posted_at=None for both entries
        assert all(item["posted_at"] is None for item in resp.json()["items"])

    async def test_list_requires_auth(self, client):
        resp = await client.get("/api/v1/job-discovery/listings")
        assert resp.status_code == 401

    async def test_list_returns_persisted_listings(self, client):
        headers = await _person_headers(client)
        await client.post("/api/v1/job-discovery/discover", json={}, headers=headers)
        resp = await client.get("/api/v1/job-discovery/listings", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 2
        titles = {item["title"] for item in resp.json()["items"]}
        assert titles == {"Systems Engineer", "Cloud Engineer (Remote)"}

    async def test_list_shows_undisclosed_salary_honestly(self, client):
        headers = await _person_headers(client)
        await client.post("/api/v1/job-discovery/discover", json={}, headers=headers)
        resp = await client.get("/api/v1/job-discovery/listings", headers=headers)
        remote_job = next(item for item in resp.json()["items"] if item["is_remote"])
        assert remote_job["salary_disclosed"] is False
        assert remote_job["salary_min"] is None

    async def test_listings_shared_across_persons_not_ownership_scoped(self, client):
        """Confirms the deliberate design: JobListing is a shared
        catalogue, not per-person data -- both users see the same
        listings after one triggers discovery."""
        headers_a = await _person_headers(client, email="jdA@example.com")
        headers_b = await _person_headers(client, email="jdB@example.com")
        await client.post("/api/v1/job-discovery/discover", json={}, headers=headers_a)
        resp_b = await client.get("/api/v1/job-discovery/listings", headers=headers_b)
        assert resp_b.json()["total"] == 2  # B sees A's discovered listings -- shared catalogue, by design

    async def test_pagination_parameters_respected(self, client):
        headers = await _person_headers(client)
        await client.post("/api/v1/job-discovery/discover", json={}, headers=headers)
        resp = await client.get("/api/v1/job-discovery/listings?limit=1&offset=0", headers=headers)
        assert len(resp.json()["items"]) == 1
        assert resp.json()["limit"] == 1
