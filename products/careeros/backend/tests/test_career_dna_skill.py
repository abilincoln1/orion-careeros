"""Tests for /career-dna/skills (public taxonomy search) and
/career-dna/person-skills (owned, authenticated CRUD).
"""
import pytest

pytestmark = pytest.mark.asyncio


async def _person_headers(client, email="skill@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret1", "full_name": "Test Person"},
    )
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret1"})
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    await client.post("/api/v1/career-dna/person", json={"first_name": "Test", "last_name": "Person"}, headers=headers)
    return headers


async def test_search_skills_does_not_require_auth(client):
    resp = await client.get("/api/v1/career-dna/skills")
    assert resp.status_code == 200
    assert resp.json()["items"] == []


async def test_add_person_skill_requires_auth(client):
    resp = await client.post(
        "/api/v1/career-dna/person-skills",
        json={"skill_name": "Python", "skill_type": "technical", "proficiency": "advanced"},
    )
    assert resp.status_code == 401


async def test_add_person_skill_creates_taxonomy_entry(client):
    headers = await _person_headers(client)
    resp = await client.post(
        "/api/v1/career-dna/person-skills",
        json={"skill_name": "Python", "skill_type": "technical", "proficiency": "advanced", "years_experience": 5},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["years_experience"] == 5

    # the skill now appears in the shared, public taxonomy search
    search = await client.get("/api/v1/career-dna/skills?q=Pyth")
    assert search.status_code == 200
    assert search.json()["total"] == 1
    assert search.json()["items"][0]["name"] == "Python"


async def test_add_duplicate_skill_rejected(client):
    headers = await _person_headers(client)
    payload = {"skill_name": "Python", "skill_type": "technical", "proficiency": "advanced"}
    first = await client.post("/api/v1/career-dna/person-skills", json=payload, headers=headers)
    assert first.status_code == 201
    second = await client.post("/api/v1/career-dna/person-skills", json=payload, headers=headers)
    assert second.status_code == 409


async def test_skill_taxonomy_deduplicated_across_persons(client):
    """Two different people adding the same skill name must resolve to the
    same underlying Skill taxonomy row (upsert-on-normalized-name), not
    create two duplicate taxonomy entries -- Architecture Review must-fix #3."""
    headers_a = await _person_headers(client, email="skillA@example.com")
    headers_b = await _person_headers(client, email="skillB@example.com")

    await client.post(
        "/api/v1/career-dna/person-skills",
        json={"skill_name": "Python", "skill_type": "technical", "proficiency": "advanced"},
        headers=headers_a,
    )
    await client.post(
        "/api/v1/career-dna/person-skills",
        json={"skill_name": "python", "skill_type": "technical", "proficiency": "advanced"},  # different case
        headers=headers_b,
    )

    search = await client.get("/api/v1/career-dna/skills?q=python")
    assert search.status_code == 200
    assert search.json()["total"] == 1, "expected a single deduplicated taxonomy row, not one per person"


async def test_list_person_skills_scoped_to_owner(client):
    headers_a = await _person_headers(client, email="listA@example.com")
    headers_b = await _person_headers(client, email="listB@example.com")

    await client.post(
        "/api/v1/career-dna/person-skills",
        json={"skill_name": "Python", "skill_type": "technical", "proficiency": "advanced"},
        headers=headers_a,
    )

    resp_a = await client.get("/api/v1/career-dna/person-skills", headers=headers_a)
    resp_b = await client.get("/api/v1/career-dna/person-skills", headers=headers_b)
    assert resp_a.json()["total"] == 1
    assert resp_b.json()["total"] == 0


async def test_update_person_skill(client):
    headers = await _person_headers(client)
    created = await client.post(
        "/api/v1/career-dna/person-skills",
        json={"skill_name": "Python", "skill_type": "technical", "proficiency": "advanced", "years_experience": 2},
        headers=headers,
    )
    person_skill_id = created.json()["id"]
    resp = await client.patch(
        f"/api/v1/career-dna/person-skills/{person_skill_id}",
        json={"years_experience": 6},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["years_experience"] == 6


async def test_attribution_source_not_client_settable(client):
    """Architecture Review must-fix #5: 'verified' must never be settable
    directly by the client -- the Create/Update schemas simply don't expose
    the field, so sending it should be silently ignored (FastAPI/Pydantic
    drops unknown fields by default), not accepted as an override."""
    headers = await _person_headers(client)
    resp = await client.post(
        "/api/v1/career-dna/person-skills",
        json={"skill_name": "Python", "skill_type": "technical", "proficiency": "advanced", "attribution_source": "verified"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["attribution_source"] == "self_reported", (
        "attribution_source must default to self_reported and ignore any client-supplied "
        "value -- accepting a client override here would defeat the evidence-backed "
        "verification model entirely (must-fix #5)"
    )


async def test_delete_person_skill(client):
    headers = await _person_headers(client)
    created = await client.post(
        "/api/v1/career-dna/person-skills",
        json={"skill_name": "Python", "skill_type": "technical", "proficiency": "advanced"},
        headers=headers,
    )
    person_skill_id = created.json()["id"]
    resp = await client.delete(f"/api/v1/career-dna/person-skills/{person_skill_id}", headers=headers)
    assert resp.status_code == 204


async def test_update_person_skill_not_found(client):
    headers = await _person_headers(client)
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.patch(
        f"/api/v1/career-dna/person-skills/{fake_id}", json={"years_experience": 1}, headers=headers
    )
    assert resp.status_code == 404


async def test_delete_person_skill_not_found(client):
    headers = await _person_headers(client)
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.delete(f"/api/v1/career-dna/person-skills/{fake_id}", headers=headers)
    assert resp.status_code == 404


async def test_list_person_skills_filtered_by_skill_type(client):
    headers = await _person_headers(client)
    await client.post(
        "/api/v1/career-dna/person-skills",
        json={"skill_name": "Python", "skill_type": "technical", "proficiency": "advanced"},
        headers=headers,
    )
    await client.post(
        "/api/v1/career-dna/person-skills",
        json={"skill_name": "Leadership", "skill_type": "soft", "proficiency": "intermediate"},
        headers=headers,
    )
    resp = await client.get("/api/v1/career-dna/person-skills?skill_type=technical", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


async def test_delete_person_skill_cleans_up_dependent_evidence_links(client):
    """Must-fix #2 (orphan cleanup): deleting a PersonSkill that has a
    linked EvidenceLink must also remove that link in the same
    transaction, since subject_id isn't a real DB-level foreign key."""
    headers = await _person_headers(client)
    skill_resp = await client.post(
        "/api/v1/career-dna/person-skills",
        json={"skill_name": "Python", "skill_type": "technical", "proficiency": "advanced"},
        headers=headers,
    )
    skill_id = skill_resp.json()["id"]
    evidence_resp = await client.post(
        "/api/v1/career-dna/evidence", json={"evidence_type": "url", "title": "Proof"}, headers=headers
    )
    evidence_id = evidence_resp.json()["id"]
    await client.post(
        f"/api/v1/career-dna/evidence/{evidence_id}/link",
        json={"subject_type": "person_skill", "subject_id": skill_id},
        headers=headers,
    )

    delete_resp = await client.delete(f"/api/v1/career-dna/person-skills/{skill_id}", headers=headers)
    assert delete_resp.status_code == 204
    # the evidence row itself remains (evidence isn't deleted, just the link) -- confirm no 500 on a follow-up read
    evidence_check = await client.get("/api/v1/career-dna/evidence", headers=headers)
    assert evidence_check.status_code == 200
