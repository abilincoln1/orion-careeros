"""Tests for POST/GET/PATCH /career-dna/person(s) and CareerProfile.

Sprint 1.6 Phase 5 -- closes the zero-coverage gap on app/services/
person_service.py and app/api/v1/career_dna/person.py identified in the
Sprint 1.5 Repository Reconciliation Report.
"""
import pytest

pytestmark = pytest.mark.asyncio


async def _register_and_login(client, email="person@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret1", "full_name": "Test Person"},
    )
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret1"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_create_person_requires_auth(client):
    resp = await client.post("/api/v1/career-dna/person", json={"first_name": "A", "last_name": "B"})
    assert resp.status_code == 401


async def test_get_me_requires_person_to_exist_first(client):
    headers = await _register_and_login(client)
    resp = await client.get("/api/v1/career-dna/person/me", headers=headers)
    assert resp.status_code == 404


async def test_create_person_success(client):
    headers = await _register_and_login(client)
    resp = await client.post(
        "/api/v1/career-dna/person",
        json={"first_name": "Ada", "last_name": "Lovelace", "headline": "Engineer"},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["first_name"] == "Ada"
    assert body["last_name"] == "Lovelace"
    assert "id" in body


async def test_create_person_duplicate_rejected(client):
    headers = await _register_and_login(client)
    payload = {"first_name": "Ada", "last_name": "Lovelace"}
    first = await client.post("/api/v1/career-dna/person", json=payload, headers=headers)
    assert first.status_code == 201
    second = await client.post("/api/v1/career-dna/person", json=payload, headers=headers)
    assert second.status_code == 409


async def test_create_person_validation_rejects_empty_names(client):
    headers = await _register_and_login(client)
    resp = await client.post(
        "/api/v1/career-dna/person", json={"first_name": "", "last_name": "Lovelace"}, headers=headers
    )
    assert resp.status_code == 422


async def test_get_me_after_create(client):
    headers = await _register_and_login(client)
    await client.post(
        "/api/v1/career-dna/person", json={"first_name": "Ada", "last_name": "Lovelace"}, headers=headers
    )
    resp = await client.get("/api/v1/career-dna/person/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Ada"


async def test_patch_me_updates_fields(client):
    headers = await _register_and_login(client)
    await client.post(
        "/api/v1/career-dna/person", json={"first_name": "Ada", "last_name": "Lovelace"}, headers=headers
    )
    resp = await client.patch(
        "/api/v1/career-dna/person/me", json={"headline": "Countess of Lovelace"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["headline"] == "Countess of Lovelace"
    # unspecified fields are unchanged
    assert resp.json()["first_name"] == "Ada"


async def test_career_profile_created_alongside_person(client):
    headers = await _register_and_login(client)
    await client.post(
        "/api/v1/career-dna/person", json={"first_name": "Ada", "last_name": "Lovelace"}, headers=headers
    )
    resp = await client.get("/api/v1/career-dna/person/me/profile", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["person_id"]


async def test_patch_career_profile(client):
    headers = await _register_and_login(client)
    await client.post(
        "/api/v1/career-dna/person", json={"first_name": "Ada", "last_name": "Lovelace"}, headers=headers
    )
    resp = await client.patch(
        "/api/v1/career-dna/person/me/profile", json={"summary": "Pioneer of computing."}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["summary"] == "Pioneer of computing."


async def test_person_scoped_to_owning_user_only(client):
    """Two different users each get their own independent Person record --
    there is no cross-user leakage through /me (which always resolves via
    the authenticated token, never a client-supplied id)."""
    headers_a = await _register_and_login(client, email="a@example.com")
    headers_b = await _register_and_login(client, email="b@example.com")

    await client.post(
        "/api/v1/career-dna/person", json={"first_name": "UserA", "last_name": "Test"}, headers=headers_a
    )
    # user B has not created a Person yet -- must 404, not see user A's record
    resp_b = await client.get("/api/v1/career-dna/person/me", headers=headers_b)
    assert resp_b.status_code == 404

    resp_a = await client.get("/api/v1/career-dna/person/me", headers=headers_a)
    assert resp_a.status_code == 200
    assert resp_a.json()["first_name"] == "UserA"


async def test_patch_me_partial_update_leaves_other_fields_unchanged(client):
    """model_dump(exclude_unset=True) semantics: PATCH with only one field
    must not null out the others."""
    headers = await _register_and_login(client)
    await client.post(
        "/api/v1/career-dna/person",
        json={"first_name": "Ada", "last_name": "Lovelace", "preferred_name": "Ada L."},
        headers=headers,
    )
    resp = await client.patch("/api/v1/career-dna/person/me", json={"last_name": "King"}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["last_name"] == "King"
    assert body["first_name"] == "Ada"
    assert body["preferred_name"] == "Ada L."


async def test_patch_me_requires_person_to_exist(client):
    headers = await _register_and_login(client)
    resp = await client.patch("/api/v1/career-dna/person/me", json={"headline": "x"}, headers=headers)
    assert resp.status_code == 404


async def test_patch_career_profile_requires_person_to_exist(client):
    headers = await _register_and_login(client)
    resp = await client.patch(
        "/api/v1/career-dna/person/me/profile", json={"summary": "x"}, headers=headers
    )
    assert resp.status_code == 404


async def test_get_career_profile_requires_person_to_exist(client):
    headers = await _register_and_login(client)
    resp = await client.get("/api/v1/career-dna/person/me/profile", headers=headers)
    assert resp.status_code == 404
