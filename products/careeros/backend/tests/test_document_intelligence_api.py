"""
Integration and API tests for the Document Intelligence Engine
(Sprint 3 Stage 1). Exercises the full pipeline -- upload -> extract ->
review -> apply -- against MockDocumentExtractionProvider, per
docs/SPRINT-3-STAGE1-TEST-STRATEGY.md. No real LLM API is ever called.
"""
from pathlib import Path

import pytest

from app.api.deps import get_extraction_provider, get_storage_adapter
from app.main import app
from orion_kernel.document_intelligence import LocalStorageAdapter, MockDocumentExtractionProvider

pytestmark = pytest.mark.asyncio

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _override_storage_and_provider(tmp_path):
    """Every test in this file gets an isolated tmp_path storage
    location (never the real configured DOCUMENT_STORAGE_PATH) and the
    'clean' mock provider fixture by default. Individual tests override
    get_extraction_provider further where they need a different
    fixture (low_confidence, partial, unhealthy)."""
    app.dependency_overrides[get_storage_adapter] = lambda: LocalStorageAdapter(tmp_path / "storage")
    app.dependency_overrides[get_extraction_provider] = lambda: MockDocumentExtractionProvider(
        fixture="clean"
    )
    yield
    app.dependency_overrides.pop(get_storage_adapter, None)
    app.dependency_overrides.pop(get_extraction_provider, None)


async def _person_headers(client, email="docintel@example.com"):
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


async def _upload_pdf(client, headers):
    content = (FIXTURES / "sample_cv.pdf").read_bytes()
    resp = await client.post(
        "/api/v1/document-intelligence/documents",
        files={"file": ("cv.pdf", content, "application/pdf")},
        headers=headers,
    )
    return resp


class TestUpload:
    async def test_upload_requires_auth(self, client):
        content = (FIXTURES / "sample_cv.pdf").read_bytes()
        resp = await client.post(
            "/api/v1/document-intelligence/documents",
            files={"file": ("cv.pdf", content, "application/pdf")},
        )
        assert resp.status_code == 401

    async def test_upload_valid_pdf_succeeds(self, client):
        headers = await _person_headers(client)
        resp = await _upload_pdf(client, headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["document_type"] == "pdf"
        assert body["status"] == "uploaded"
        assert len(body["versions"]) == 1
        assert body["versions"][0]["version_number"] == 1

    async def test_upload_valid_docx_succeeds(self, client):
        headers = await _person_headers(client)
        content = (FIXTURES / "sample_cv.docx").read_bytes()
        resp = await client.post(
            "/api/v1/document-intelligence/documents",
            files={
                "file": (
                    "cv.docx", content,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["document_type"] == "docx"

    async def test_upload_unsupported_type_rejected(self, client):
        headers = await _person_headers(client)
        resp = await client.post(
            "/api/v1/document-intelligence/documents",
            files={"file": ("cv.txt", b"plain text", "text/plain")},
            headers=headers,
        )
        assert resp.status_code == 422

    async def test_upload_mismatched_content_rejected(self, client):
        """A .pdf extension whose content isn't actually a PDF must be
        rejected at the API layer with 422, not crash into a 500 --
        confirms StorageValidationError is actually caught, not just
        raised into the void."""
        headers = await _person_headers(client)
        resp = await client.post(
            "/api/v1/document-intelligence/documents",
            files={"file": ("cv.pdf", b"not a real pdf", "application/pdf")},
            headers=headers,
        )
        assert resp.status_code == 422


class TestListAndGet:
    async def test_list_documents_scoped_to_owner(self, client):
        headers_a = await _person_headers(client, email="listA@example.com")
        headers_b = await _person_headers(client, email="listB@example.com")
        await _upload_pdf(client, headers_a)

        resp_a = await client.get("/api/v1/document-intelligence/documents", headers=headers_a)
        resp_b = await client.get("/api/v1/document-intelligence/documents", headers=headers_b)
        assert len(resp_a.json()) == 1
        assert len(resp_b.json()) == 0

    async def test_get_document_not_found(self, client):
        headers = await _person_headers(client)
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(f"/api/v1/document-intelligence/documents/{fake_id}", headers=headers)
        assert resp.status_code == 404

    async def test_get_document_cross_user_isolation(self, client):
        headers_a = await _person_headers(client, email="getA@example.com")
        headers_b = await _person_headers(client, email="getB@example.com")
        upload = await _upload_pdf(client, headers_a)
        document_id = upload.json()["id"]

        resp = await client.get(
            f"/api/v1/document-intelligence/documents/{document_id}", headers=headers_b
        )
        assert resp.status_code == 404


class TestExtraction:
    async def test_extract_runs_and_returns_completed_run(self, client):
        headers = await _person_headers(client)
        upload = await _upload_pdf(client, headers)
        document_id = upload.json()["id"]

        resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/extract", headers=headers
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "completed"
        assert body["provider_name"] == "mock"
        assert body["run_number"] == 1
        assert body["overall_confidence"] > 0.9
        assert body["extraction_result"]["persons"][0]["first_name"]["value"] == "Ada"

    async def test_extract_marks_document_extracted(self, client):
        headers = await _person_headers(client)
        upload = await _upload_pdf(client, headers)
        document_id = upload.json()["id"]
        await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/extract", headers=headers
        )
        doc = await client.get(f"/api/v1/document-intelligence/documents/{document_id}", headers=headers)
        assert doc.json()["status"] == "extracted"

    async def test_second_extraction_increments_run_number(self, client):
        headers = await _person_headers(client)
        upload = await _upload_pdf(client, headers)
        document_id = upload.json()["id"]
        first = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/extract", headers=headers
        )
        second = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/extract", headers=headers
        )
        assert first.json()["run_number"] == 1
        assert second.json()["run_number"] == 2

    async def test_extraction_failure_recorded_not_500(self, client):
        """A provider configured to fail must produce a run with
        status=failed and an error_detail, never an unhandled 500."""
        headers = await _person_headers(client)
        upload = await _upload_pdf(client, headers)
        document_id = upload.json()["id"]

        app.dependency_overrides[get_extraction_provider] = lambda: MockDocumentExtractionProvider(
            healthy=False
        )
        resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/extract", headers=headers
        )
        assert resp.status_code == 201  # the RUN was created successfully; ITS status reflects failure
        assert resp.json()["status"] == "failed"
        assert resp.json()["error_detail"]

    async def test_get_run_for_review(self, client):
        headers = await _person_headers(client)
        upload = await _upload_pdf(client, headers)
        document_id = upload.json()["id"]
        extract_resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/extract", headers=headers
        )
        run_id = extract_resp.json()["id"]

        resp = await client.get(
            f"/api/v1/document-intelligence/documents/{document_id}/runs/{run_id}", headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["extraction_result"] is not None


class TestApply:
    async def test_apply_before_extract_is_impossible(self, client):
        """There is no run to apply until extract() has been called --
        confirms extraction and application are genuinely separate
        steps, per the human review workflow requirement."""
        headers = await _person_headers(client)
        upload = await _upload_pdf(client, headers)
        document_id = upload.json()["id"]
        fake_run_id = "00000000-0000-0000-0000-000000000000"

        resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/runs/{fake_run_id}/apply",
            headers=headers,
        )
        assert resp.status_code == 404

    async def test_apply_updates_person_headline_when_unset(self, client):
        headers = await _person_headers(client)
        upload = await _upload_pdf(client, headers)
        document_id = upload.json()["id"]
        extract_resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/extract", headers=headers
        )
        run_id = extract_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/runs/{run_id}/apply",
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["person_updated"] is True

        person = await client.get("/api/v1/career-dna/person/me", headers=headers)
        assert person.json()["headline"] == "Software Engineer"

    async def test_apply_does_not_overwrite_existing_headline(self, client):
        """Must never silently replace a value the person already
        entered themselves with an AI-extracted guess."""
        headers = await _person_headers(client)
        await client.patch(
            "/api/v1/career-dna/person/me", json={"headline": "My Own Headline"}, headers=headers
        )
        upload = await _upload_pdf(client, headers)
        document_id = upload.json()["id"]
        extract_resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/extract", headers=headers
        )
        run_id = extract_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/runs/{run_id}/apply",
            headers=headers,
        )
        assert resp.json()["person_updated"] is False

        person = await client.get("/api/v1/career-dna/person/me", headers=headers)
        assert person.json()["headline"] == "My Own Headline"

    async def test_apply_persists_employment_and_skills_with_ai_extracted_provenance(self, client):
        """TD-023 Option B: the response must confirm employment and
        skills were actually written to Career DNA, and the resulting
        records must carry attribution_source=ai_extracted -- not just
        a summary count, but the real persisted records checked via the
        existing Career DNA API."""
        headers = await _person_headers(client)
        upload = await _upload_pdf(client, headers)
        document_id = upload.json()["id"]
        extract_resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/extract", headers=headers
        )
        run_id = extract_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/runs/{run_id}/apply",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["employments_applied"] == 1
        assert body["skills_applied"] == 2  # the "clean" fixture has 2 skills
        assert body["employments_skipped_conflict"] == 0
        assert body["skills_skipped_duplicate"] == 0

        # confirm via the real Career DNA API -- not just the apply() summary
        employments = await client.get("/api/v1/career-dna/employments", headers=headers)
        assert employments.json()["total"] == 1
        assert employments.json()["items"][0]["attribution_source"] == "ai_extracted"
        assert employments.json()["items"][0]["role_title_raw"] == "Software Engineer"

        skills = await client.get("/api/v1/career-dna/person-skills", headers=headers)
        assert skills.json()["total"] == 2
        assert all(s["attribution_source"] == "ai_extracted" for s in skills.json()["items"])

    async def test_apply_defaults_undetermined_employment_type_and_discloses_it(self, client):
        """The mock 'clean' fixture doesn't specify employment_type --
        confirms the fallback is applied AND disclosed in the note,
        never silent."""
        headers = await _person_headers(client)
        upload = await _upload_pdf(client, headers)
        document_id = upload.json()["id"]
        extract_resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/extract", headers=headers
        )
        run_id = extract_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/runs/{run_id}/apply",
            headers=headers,
        )
        assert "employment_type" in resp.json()["note"]
        assert "full_time" in resp.json()["note"]

    async def test_apply_does_not_duplicate_skill_already_on_person(self, client):
        """A skill the person already has (manually entered) must be
        skipped, not duplicated or overwritten, when the same skill name
        is also extracted from a CV."""
        headers = await _person_headers(client)
        await client.post(
            "/api/v1/career-dna/person-skills",
            json={"skill_name": "Python", "skill_type": "technical", "proficiency": "advanced"},
            headers=headers,
        )
        upload = await _upload_pdf(client, headers)
        document_id = upload.json()["id"]
        extract_resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/extract", headers=headers
        )
        run_id = extract_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/runs/{run_id}/apply",
            headers=headers,
        )
        body = resp.json()
        assert body["skills_skipped_duplicate"] == 1  # "Python" already existed
        assert body["skills_applied"] == 1  # "SQL" is new

        skills = await client.get("/api/v1/career-dna/person-skills", headers=headers)
        assert skills.json()["total"] == 2
        # the manually-entered Python skill must retain its ORIGINAL
        # attribution -- confirms apply() genuinely skips, not overwrites
        python_skill = next(s for s in skills.json()["items"] if s["proficiency"] == "advanced")
        assert python_skill["attribution_source"] == "self_reported"

    async def test_apply_skips_employment_conflicting_with_existing_primary_current(self, client):
        """A pre-existing primary current employment (manually entered)
        must not be silently overwritten or duplicated by a conflicting
        extracted 'is_current' employment -- the existing Sprint 2
        DB-level constraint is respected, and the conflict is reported,
        not hidden."""
        headers = await _person_headers(client)
        await client.post(
            "/api/v1/career-dna/employments",
            json={
                "employer_name": "Existing Corp",
                "role_title": "Existing Role",
                "employment_type": "full_time",
                "start_date": "2020-01-01",
                "is_current": True,
            },
            headers=headers,
        )
        upload = await _upload_pdf(client, headers)
        document_id = upload.json()["id"]
        extract_resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/extract", headers=headers
        )
        run_id = extract_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/runs/{run_id}/apply",
            headers=headers,
        )
        body = resp.json()
        assert body["employments_skipped_conflict"] == 1
        assert body["employments_applied"] == 0
        assert "conflicted" in body["note"].lower()

        employments = await client.get("/api/v1/career-dna/employments", headers=headers)
        assert employments.json()["total"] == 1  # only the original, manually-entered one
        assert employments.json()["items"][0]["role_title_raw"] == "Existing Role"
        assert employments.json()["items"][0]["attribution_source"] == "self_reported"

    async def test_manually_created_employment_still_defaults_to_self_reported(self, client):
        """Regression: the existing, unmodified public API (no
        attribution_source in the request body) must continue to
        produce self_reported records exactly as before TD-023 Option B."""
        headers = await _person_headers(client)
        resp = await client.post(
            "/api/v1/career-dna/employments",
            json={
                "employer_name": "Regular Corp",
                "role_title": "Regular Role",
                "employment_type": "full_time",
                "start_date": "2021-01-01",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["attribution_source"] == "self_reported"

    async def test_manually_created_skill_still_defaults_to_self_reported(self, client):
        """Regression: confirms must-fix #5's original guarantee is
        completely unchanged by this fix."""
        headers = await _person_headers(client)
        resp = await client.post(
            "/api/v1/career-dna/person-skills",
            json={"skill_name": "Rust", "skill_type": "technical", "proficiency": "beginner"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["attribution_source"] == "self_reported"

    async def test_apply_twice_rejected(self, client):
        headers = await _person_headers(client)
        upload = await _upload_pdf(client, headers)
        document_id = upload.json()["id"]
        extract_resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/extract", headers=headers
        )
        run_id = extract_resp.json()["id"]

        first = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/runs/{run_id}/apply",
            headers=headers,
        )
        second = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/runs/{run_id}/apply",
            headers=headers,
        )
        assert first.status_code == 200
        assert second.status_code == 409

    async def test_apply_failed_run_rejected(self, client):
        headers = await _person_headers(client)
        upload = await _upload_pdf(client, headers)
        document_id = upload.json()["id"]

        app.dependency_overrides[get_extraction_provider] = lambda: MockDocumentExtractionProvider(
            healthy=False
        )
        extract_resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/extract", headers=headers
        )
        run_id = extract_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/document-intelligence/documents/{document_id}/runs/{run_id}/apply",
            headers=headers,
        )
        assert resp.status_code == 409
