"""Tests for /career-dna/evidence -- creation, linking to a PersonSkill
(and the attribution_source auto-promotion to 'verified' this triggers,
per Architecture Review must-fix #5), unlinking, and deletion.
"""
import pytest

pytestmark = pytest.mark.asyncio


async def _person_headers(client, email="evidence@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret1", "full_name": "Test Person"},
    )
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret1"})
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    await client.post("/api/v1/career-dna/person", json={"first_name": "Test", "last_name": "Person"}, headers=headers)
    return headers


async def _add_skill(client, headers, name="Python"):
    resp = await client.post(
        "/api/v1/career-dna/person-skills",
        json={"skill_name": name, "skill_type": "technical", "proficiency": "advanced"},
        headers=headers,
    )
    return resp.json()["id"]


async def test_create_evidence_requires_auth(client):
    resp = await client.post(
        "/api/v1/career-dna/evidence", json={"evidence_type": "url", "title": "GitHub repo"}
    )
    assert resp.status_code == 401


async def test_create_evidence_success(client):
    headers = await _person_headers(client)
    resp = await client.post(
        "/api/v1/career-dna/evidence",
        json={"evidence_type": "url", "title": "GitHub repo", "source_url": "https://github.com/example"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "GitHub repo"


async def test_list_evidence_scoped_to_owner(client):
    headers_a = await _person_headers(client, email="evA@example.com")
    headers_b = await _person_headers(client, email="evB@example.com")
    await client.post(
        "/api/v1/career-dna/evidence", json={"evidence_type": "url", "title": "A's evidence"}, headers=headers_a
    )
    resp_a = await client.get("/api/v1/career-dna/evidence", headers=headers_a)
    resp_b = await client.get("/api/v1/career-dna/evidence", headers=headers_b)
    assert resp_a.json()["total"] == 1
    assert resp_b.json()["total"] == 0


async def test_link_evidence_promotes_attribution_to_verified(client):
    """Core guarantee of must-fix #5: linking qualifying evidence to a
    PersonSkill is the ONLY way attribution_source becomes 'verified' --
    there is no direct client-settable path."""
    headers = await _person_headers(client)
    skill_id = await _add_skill(client, headers)

    before = await client.get("/api/v1/career-dna/person-skills", headers=headers)
    assert before.json()["items"][0]["attribution_source"] == "self_reported"

    evidence = await client.post(
        "/api/v1/career-dna/evidence",
        json={"evidence_type": "url", "title": "Portfolio project"},
        headers=headers,
    )
    evidence_id = evidence.json()["id"]

    link_resp = await client.post(
        f"/api/v1/career-dna/evidence/{evidence_id}/link",
        json={"subject_type": "person_skill", "subject_id": skill_id},
        headers=headers,
    )
    assert link_resp.status_code == 201

    after = await client.get("/api/v1/career-dna/person-skills", headers=headers)
    assert after.json()["items"][0]["attribution_source"] == "verified", (
        "linking evidence must auto-promote attribution_source to verified -- "
        "this is the only legitimate path to 'verified' per must-fix #5"
    )


async def test_unlink_evidence(client):
    headers = await _person_headers(client)
    skill_id = await _add_skill(client, headers)
    evidence = await client.post(
        "/api/v1/career-dna/evidence", json={"evidence_type": "url", "title": "Proof"}, headers=headers
    )
    evidence_id = evidence.json()["id"]
    link = await client.post(
        f"/api/v1/career-dna/evidence/{evidence_id}/link",
        json={"subject_type": "person_skill", "subject_id": skill_id},
        headers=headers,
    )
    link_id = link.json()["id"]

    resp = await client.delete(
        f"/api/v1/career-dna/evidence/{evidence_id}/link/{link_id}", headers=headers
    )
    assert resp.status_code == 204


async def test_delete_evidence(client):
    headers = await _person_headers(client)
    evidence = await client.post(
        "/api/v1/career-dna/evidence", json={"evidence_type": "url", "title": "Temp"}, headers=headers
    )
    evidence_id = evidence.json()["id"]
    resp = await client.delete(f"/api/v1/career-dna/evidence/{evidence_id}", headers=headers)
    assert resp.status_code == 204


async def test_evidence_title_validation(client):
    headers = await _person_headers(client)
    resp = await client.post(
        "/api/v1/career-dna/evidence", json={"evidence_type": "url", "title": ""}, headers=headers
    )
    assert resp.status_code == 422


async def test_get_evidence_not_found_via_link_attempt(client):
    headers = await _person_headers(client)
    fake_evidence_id = "00000000-0000-0000-0000-000000000000"
    fake_skill_id = "00000000-0000-0000-0000-000000000001"
    resp = await client.post(
        f"/api/v1/career-dna/evidence/{fake_evidence_id}/link",
        json={"subject_type": "person_skill", "subject_id": fake_skill_id},
        headers=headers,
    )
    assert resp.status_code == 404


async def test_link_to_nonexistent_subject_rejected(client):
    headers = await _person_headers(client)
    evidence = await client.post(
        "/api/v1/career-dna/evidence", json={"evidence_type": "url", "title": "Proof"}, headers=headers
    )
    evidence_id = evidence.json()["id"]
    fake_skill_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.post(
        f"/api/v1/career-dna/evidence/{evidence_id}/link",
        json={"subject_type": "person_skill", "subject_id": fake_skill_id},
        headers=headers,
    )
    assert resp.status_code == 404


async def test_unlink_evidence_not_found(client):
    headers = await _person_headers(client)
    evidence = await client.post(
        "/api/v1/career-dna/evidence", json={"evidence_type": "url", "title": "Proof"}, headers=headers
    )
    evidence_id = evidence.json()["id"]
    fake_link_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.delete(
        f"/api/v1/career-dna/evidence/{evidence_id}/link/{fake_link_id}", headers=headers
    )
    assert resp.status_code == 404


async def test_unlink_demotes_verified_back_to_inferred(client):
    """_recompute_attribution: removing the last EvidenceLink for a subject
    that was VERIFIED demotes it back to INFERRED (not self_reported --
    the module docstring is explicit that self_reported is never touched
    by this function)."""
    headers = await _person_headers(client)
    skill = await client.post(
        "/api/v1/career-dna/person-skills",
        json={"skill_name": "Python", "skill_type": "technical", "proficiency": "advanced"},
        headers=headers,
    )
    skill_id = skill.json()["id"]
    evidence = await client.post(
        "/api/v1/career-dna/evidence", json={"evidence_type": "url", "title": "Proof"}, headers=headers
    )
    evidence_id = evidence.json()["id"]
    link = await client.post(
        f"/api/v1/career-dna/evidence/{evidence_id}/link",
        json={"subject_type": "person_skill", "subject_id": skill_id},
        headers=headers,
    )
    link_id = link.json()["id"]

    mid = await client.get("/api/v1/career-dna/person-skills", headers=headers)
    assert mid.json()["items"][0]["attribution_source"] == "verified"

    await client.delete(f"/api/v1/career-dna/evidence/{evidence_id}/link/{link_id}", headers=headers)

    after = await client.get("/api/v1/career-dna/person-skills", headers=headers)
    assert after.json()["items"][0]["attribution_source"] == "inferred", (
        "removing the only evidence link for a VERIFIED subject must demote it to "
        "INFERRED, per _recompute_attribution's documented behavior"
    )


async def test_delete_evidence_cascades_and_demotes_dependent_skill(client):
    """delete_evidence: deleting Evidence that was the sole proof behind a
    VERIFIED PersonSkill must demote that skill back to INFERRED, even
    though the EvidenceLink itself is removed via DB-level CASCADE, not
    application code -- the service must recompute attribution using the
    subject list captured BEFORE the delete."""
    headers = await _person_headers(client)
    skill = await client.post(
        "/api/v1/career-dna/person-skills",
        json={"skill_name": "Python", "skill_type": "technical", "proficiency": "advanced"},
        headers=headers,
    )
    skill_id = skill.json()["id"]
    evidence = await client.post(
        "/api/v1/career-dna/evidence", json={"evidence_type": "url", "title": "Proof"}, headers=headers
    )
    evidence_id = evidence.json()["id"]
    await client.post(
        f"/api/v1/career-dna/evidence/{evidence_id}/link",
        json={"subject_type": "person_skill", "subject_id": skill_id},
        headers=headers,
    )

    delete_resp = await client.delete(f"/api/v1/career-dna/evidence/{evidence_id}", headers=headers)
    assert delete_resp.status_code == 204

    after = await client.get("/api/v1/career-dna/person-skills", headers=headers)
    assert after.json()["items"][0]["attribution_source"] == "inferred"


async def test_delete_evidence_not_found(client):
    headers = await _person_headers(client)
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.delete(f"/api/v1/career-dna/evidence/{fake_id}", headers=headers)
    assert resp.status_code == 404


async def test_evidence_scoped_to_owning_person(client):
    headers_a = await _person_headers(client, email="evScopeA@example.com")
    headers_b = await _person_headers(client, email="evScopeB@example.com")
    created = await client.post(
        "/api/v1/career-dna/evidence", json={"evidence_type": "url", "title": "A's evidence"}, headers=headers_a
    )
    evidence_id = created.json()["id"]
    resp = await client.get(f"/api/v1/career-dna/evidence/{evidence_id}", headers=headers_b)
    # no GET-by-id endpoint exists for evidence; confirm via list instead that B sees nothing
    listing_b = await client.get("/api/v1/career-dna/evidence", headers=headers_b)
    assert listing_b.json()["total"] == 0
