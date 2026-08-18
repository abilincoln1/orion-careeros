"""
Tests for ArbeitnowProvider. Uses httpx.MockTransport -- no real
network call ever happens in this file, per Section 14's "malformed
provider response" / "provider failure" requirements needing
deterministic, reproducible responses. Real network verification
happens separately, on the project owner's machine (Section 15).
"""
import httpx
import pytest

from app.job_discovery.arbeitnow_provider import ArbeitnowProvider
from app.job_discovery.provider import JobProviderFetchError

pytestmark = pytest.mark.asyncio


def _client_with_response(json_body=None, status_code=200, raise_transport_error=False):
    def handler(request: httpx.Request) -> httpx.Response:
        if raise_transport_error:
            raise httpx.ConnectError("simulated network failure")
        return httpx.Response(status_code, json=json_body)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


_SAMPLE_RESPONSE = {
    "data": [
        {
            "slug": "acme-python-dev-123",
            "title": "Python Developer",
            "company_name": "Acme Corp",
            "location": "Berlin",
            "remote": False,
            "url": "https://arbeitnow.com/jobs/acme-python-dev-123",
            "tags": ["python", "backend"],
            "description": "A Python role.",
            "salary_min": 50000,
            "salary_max": 70000,
        },
        {
            "slug": "remote-devops-456",
            "title": "DevOps Engineer",
            "company_name": "Remote Co",
            "location": "Remote",
            "remote": True,
            "url": "https://arbeitnow.com/jobs/remote-devops-456",
            "tags": ["devops", "aws"],
            "description": "Fully remote DevOps role.",
            # no salary fields at all -- must be treated as undisclosed
        },
    ]
}


class TestSuccessfulRetrieval:
    async def test_returns_all_listings_for_empty_query(self):
        client = _client_with_response(_SAMPLE_RESPONSE)
        provider = ArbeitnowProvider(http_client=client)
        results = await provider.search(query="", location=None, remote_only=False)
        assert len(results) == 2
        await client.aclose()

    async def test_filters_by_query_against_title_and_tags(self):
        client = _client_with_response(_SAMPLE_RESPONSE)
        provider = ArbeitnowProvider(http_client=client)
        results = await provider.search(query="devops", location=None, remote_only=False)
        assert len(results) == 1
        assert results[0].title == "DevOps Engineer"
        await client.aclose()

    async def test_multi_word_query_matches_on_any_significant_word_not_the_full_phrase(self):
        """Real bug found via live user testing: the original
        implementation required the ENTIRE multi-word query to appear
        verbatim, which returned zero results for any realistic
        CV-derived job title. 'Python Developer' should match
        'Python Developer' via the word 'python' even though the
        listing's exact title differs."""
        client = _client_with_response(_SAMPLE_RESPONSE)
        provider = ArbeitnowProvider(http_client=client)
        results = await provider.search(
            query="Technology Analyst - Python Developer", location=None, remote_only=False
        )
        assert len(results) == 1
        assert results[0].title == "Python Developer"
        await client.aclose()

    async def test_query_with_no_matching_words_returns_empty(self):
        client = _client_with_response(_SAMPLE_RESPONSE)
        provider = ArbeitnowProvider(http_client=client)
        results = await provider.search(query="Marketing Executive", location=None, remote_only=False)
        assert results == []
        await client.aclose()

    async def test_query_that_is_only_short_or_punctuation_words_does_not_filter_at_all(self):
        """A query like '- - -' should not accidentally exclude
        everything (or match everything by accident) -- treated the
        same as no query, per 'do not invent/exclude on uncertain
        data'."""
        client = _client_with_response(_SAMPLE_RESPONSE)
        provider = ArbeitnowProvider(http_client=client)
        results = await provider.search(query="- - -", location=None, remote_only=False)
        assert len(results) == 2  # both sample listings returned, unfiltered
        await client.aclose()

    async def test_remote_only_filter(self):
        client = _client_with_response(_SAMPLE_RESPONSE)
        provider = ArbeitnowProvider(http_client=client)
        results = await provider.search(query="", location=None, remote_only=True)
        assert len(results) == 1
        assert results[0].is_remote is True
        await client.aclose()

    async def test_salary_disclosed_when_present(self):
        client = _client_with_response(_SAMPLE_RESPONSE)
        provider = ArbeitnowProvider(http_client=client)
        results = await provider.search(query="python", location=None, remote_only=False)
        assert results[0].salary_disclosed is True
        assert results[0].salary_min == 50000
        assert results[0].salary_max == 70000
        await client.aclose()

    async def test_missing_salary_never_invented(self):
        """Section 4: 'do not invent one; do not infer an exact
        salary; retain the listing; mark salary as unknown/not
        disclosed.'"""
        client = _client_with_response(_SAMPLE_RESPONSE)
        provider = ArbeitnowProvider(http_client=client)
        results = await provider.search(query="devops", location=None, remote_only=False)
        assert results[0].salary_disclosed is False
        assert results[0].salary_min is None
        assert results[0].salary_max is None
        await client.aclose()


class TestMalformedResponse:
    async def test_missing_data_key_treated_as_empty(self):
        client = _client_with_response({"unexpected": "shape"})
        provider = ArbeitnowProvider(http_client=client)
        results = await provider.search(query="", location=None, remote_only=False)
        assert results == []
        await client.aclose()

    async def test_data_not_a_list_raises_fetch_error(self):
        client = _client_with_response({"data": "not-a-list"})
        provider = ArbeitnowProvider(http_client=client)
        with pytest.raises(JobProviderFetchError):
            await provider.search(query="", location=None, remote_only=False)
        await client.aclose()

    async def test_item_missing_title_or_slug_skipped_not_fatal(self):
        client = _client_with_response({"data": [{"company_name": "No Title Co"}]})
        provider = ArbeitnowProvider(http_client=client)
        results = await provider.search(query="", location=None, remote_only=False)
        assert results == []  # skipped, not invented, not a crash
        await client.aclose()

    async def test_non_dict_item_in_data_skipped(self):
        client = _client_with_response({"data": ["not-a-dict", 123]})
        provider = ArbeitnowProvider(http_client=client)
        results = await provider.search(query="", location=None, remote_only=False)
        assert results == []
        await client.aclose()


class TestPostedAtMapping:
    """Section 1 remediation (15 August 2026 directive): created_at ->
    posted_at, confirmed against a real captured payload, documented
    honestly as not confirmed against official API docs (no access)."""

    async def test_real_captured_timestamp_maps_correctly(self):
        """The exact value captured from a real live API response
        during Section B's verification (1786743028), confirmed to
        convert to 2026-08-14T21:30:28+00:00 -- a real, plausible date."""
        response = dict(_SAMPLE_RESPONSE)
        response["data"] = [dict(response["data"][0], created_at=1786743028)]
        client = _client_with_response(response)
        provider = ArbeitnowProvider(http_client=client)
        results = await provider.search(query="", location=None, remote_only=False)
        assert results[0].posted_at == "2026-08-14T21:30:28+00:00"
        await client.aclose()

    async def test_missing_created_at_yields_none_not_invented(self):
        client = _client_with_response(_SAMPLE_RESPONSE)  # no created_at field at all
        provider = ArbeitnowProvider(http_client=client)
        results = await provider.search(query="", location=None, remote_only=False)
        assert all(r.posted_at is None for r in results)
        await client.aclose()

    async def test_non_numeric_created_at_yields_none_not_a_crash(self):
        response = dict(_SAMPLE_RESPONSE)
        response["data"] = [dict(response["data"][0], created_at="not-a-timestamp")]
        client = _client_with_response(response)
        provider = ArbeitnowProvider(http_client=client)
        results = await provider.search(query="", location=None, remote_only=False)
        assert results[0].posted_at is None
        await client.aclose()

    async def test_implausible_future_timestamp_rejected(self):
        """A job board timestamp far in the future is not trusted
        blindly -- per the directive's 'do not invent dates' instruction,
        an implausible value is dropped, not silently accepted."""
        response = dict(_SAMPLE_RESPONSE)
        far_future = 4102444800  # year 2100
        response["data"] = [dict(response["data"][0], created_at=far_future)]
        client = _client_with_response(response)
        provider = ArbeitnowProvider(http_client=client)
        results = await provider.search(query="", location=None, remote_only=False)
        assert results[0].posted_at is None
        await client.aclose()

    async def test_implausible_pre_2000_timestamp_rejected(self):
        response = dict(_SAMPLE_RESPONSE)
        response["data"] = [dict(response["data"][0], created_at=0)]  # 1970
        client = _client_with_response(response)
        provider = ArbeitnowProvider(http_client=client)
        results = await provider.search(query="", location=None, remote_only=False)
        assert results[0].posted_at is None
        await client.aclose()
    async def test_network_error_raises_job_provider_fetch_error(self):
        client = _client_with_response(raise_transport_error=True)
        provider = ArbeitnowProvider(http_client=client)
        with pytest.raises(JobProviderFetchError):
            await provider.search(query="", location=None, remote_only=False)
        await client.aclose()

    async def test_non_200_status_raises_fetch_error(self):
        client = _client_with_response(json_body={}, status_code=503)
        provider = ArbeitnowProvider(http_client=client)
        with pytest.raises(JobProviderFetchError):
            await provider.search(query="", location=None, remote_only=False)
        await client.aclose()

    async def test_health_check_false_on_failure(self):
        client = _client_with_response(raise_transport_error=True)
        provider = ArbeitnowProvider(http_client=client)
        assert await provider.health_check() is False
        await client.aclose()

    async def test_health_check_true_on_success(self):
        client = _client_with_response(_SAMPLE_RESPONSE)
        provider = ArbeitnowProvider(http_client=client)
        assert await provider.health_check() is True
        await client.aclose()
