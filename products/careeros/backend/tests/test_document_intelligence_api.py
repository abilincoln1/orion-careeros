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

    async def test_apply_reports_skills_and_employments_not_applied(self, client):
        """TD-023: the response must honestly report what was NOT
        written to Career DNA and why -- never silently imply more
        happened than actually did."""
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
        body = resp.json()
        assert body["skills_applied"] == 0
        assert body["employments_extracted_not_applied"] == 1
        assert "TD-023" in body["note"] or "attribution" in body["note"].lower()

        # confirm the skills genuinely were not written to Career DNA
        skills = await client.get("/api/v1/career-dna/person-skills", headers=headers)
        assert skills.json()["total"] == 0

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
