"""Tests for /career-dna/employments -- CRUD plus the /promote chaining
operation (Architecture Review must-fix #1: promotions are always a new
linked row, never an in-place title edit).
"""
import pytest

pytestmark = pytest.mark.asyncio


async def _person_headers(client, email="employment@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret1", "full_name": "Test Person"},
    )
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret1"})
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    await client.post("/api/v1/career-dna/person", json={"first_name": "Test", "last_name": "Person"}, headers=headers)
    return headers


BASE_EMPLOYMENT = {
    "employer_name": "Acme Corp",
    "role_title": "Software Engineer",
    "employment_type": "full_time",
    "start_date": "2020-01-01",
    "is_current": True,
}


async def test_create_employment_requires_person(client):
    await client.post(
        "/api/v1/auth/register", json={"email": "noperson@example.com", "password": "supersecret1"}
    )
    resp = await client.post("/api/v1/auth/login", json={"email": "noperson@example.com", "password": "supersecret1"})
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    resp = await client.post("/api/v1/career-dna/employments", json=BASE_EMPLOYMENT, headers=headers)
    assert resp.status_code == 404  # get_current_person 404s if Person doesn't exist yet


async def test_create_employment_success(client):
    headers = await _person_headers(client)
    resp = await client.post("/api/v1/career-dna/employments", json=BASE_EMPLOYMENT, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["role_title_raw"] == "Software Engineer"
    assert body["is_current"] is True


async def test_end_date_before_start_date_rejected(client):
    headers = await _person_headers(client)
    payload = dict(BASE_EMPLOYMENT, start_date="2022-01-01", end_date="2021-01-01", is_current=False)
    resp = await client.post("/api/v1/career-dna/employments", json=payload, headers=headers)
    assert resp.status_code == 422


async def test_list_employments_pagination(client):
    headers = await _person_headers(client)
    await client.post("/api/v1/career-dna/employments", json=BASE_EMPLOYMENT, headers=headers)
    resp = await client.get("/api/v1/career-dna/employments", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["limit"] == 50
    assert body["offset"] == 0


async def test_get_employment_by_id(client):
    headers = await _person_headers(client)
    created = await client.post("/api/v1/career-dna/employments", json=BASE_EMPLOYMENT, headers=headers)
    employment_id = created.json()["id"]
    resp = await client.get(f"/api/v1/career-dna/employments/{employment_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == employment_id


async def test_get_employment_not_found(client):
    headers = await _person_headers(client)
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.get(f"/api/v1/career-dna/employments/{fake_id}", headers=headers)
    assert resp.status_code == 404


async def test_update_employment_description(client):
    headers = await _person_headers(client)
    created = await client.post("/api/v1/career-dna/employments", json=BASE_EMPLOYMENT, headers=headers)
    employment_id = created.json()["id"]
    resp = await client.patch(
        f"/api/v1/career-dna/employments/{employment_id}", json={"description": "Backend focus"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "Backend focus"


async def test_promote_creates_new_chained_row_not_in_place_edit(client):
    """Core architectural guarantee (must-fix #1): the original row's
    role_title must NOT change; a new row is created instead, chained via
    previous_employment_id, and the original is closed out (is_current
    False, end_date set)."""
    headers = await _person_headers(client)
    created = await client.post("/api/v1/career-dna/employments", json=BASE_EMPLOYMENT, headers=headers)
    original_id = created.json()["id"]

    promote_resp = await client.post(
        f"/api/v1/career-dna/employments/{original_id}/promote",
        json={"new_role_title": "Senior Software Engineer", "effective_date": "2023-01-01"},
        headers=headers,
    )
    assert promote_resp.status_code == 201
    new_row = promote_resp.json()
    assert new_row["role_title_raw"] == "Senior Software Engineer"
    assert new_row["id"] != original_id

    # the ORIGINAL row must be unchanged in title, and closed out
    original_after = await client.get(f"/api/v1/career-dna/employments/{original_id}", headers=headers)
    original_body = original_after.json()
    assert original_body["role_title_raw"] == "Software Engineer", (
        "promote() must not edit the original row's title in place -- "
        "this is the exact defect Architecture Review must-fix #1 exists to prevent"
    )
    assert original_body["is_current"] is False
    assert original_body["end_date"] == "2023-01-01"


async def test_delete_employment(client):
    headers = await _person_headers(client)
    created = await client.post("/api/v1/career-dna/employments", json=BASE_EMPLOYMENT, headers=headers)
    employment_id = created.json()["id"]
    resp = await client.delete(f"/api/v1/career-dna/employments/{employment_id}", headers=headers)
    assert resp.status_code == 204
    follow_up = await client.get(f"/api/v1/career-dna/employments/{employment_id}", headers=headers)
    assert follow_up.status_code == 404


async def test_second_primary_current_employment_rejected(client):
    """DB-level partial unique index: a person can have at most one
    primary (full-time/part-time) current employment at a time."""
    headers = await _person_headers(client)
    first = await client.post("/api/v1/career-dna/employments", json=BASE_EMPLOYMENT, headers=headers)
    assert first.status_code == 201

    second = dict(BASE_EMPLOYMENT, employer_name="Other Corp")
    resp = await client.post("/api/v1/career-dna/employments", json=second, headers=headers)
    assert resp.status_code == 409


async def test_promote_effective_date_before_start_rejected(client):
    headers = await _person_headers(client)
    created = await client.post("/api/v1/career-dna/employments", json=BASE_EMPLOYMENT, headers=headers)
    employment_id = created.json()["id"]
    resp = await client.post(
        f"/api/v1/career-dna/employments/{employment_id}/promote",
        json={"new_role_title": "Senior Engineer", "effective_date": "2019-01-01"},  # before start_date
        headers=headers,
    )
    assert resp.status_code == 422


async def test_promote_conflicts_with_existing_primary_current(client):
    """Promoting into a new 'is_current=True' row must respect the same
    one-primary-current-employment constraint as creation."""
    headers = await _person_headers(client)
    first = await client.post("/api/v1/career-dna/employments", json=BASE_EMPLOYMENT, headers=headers)
    first_id = first.json()["id"]

    # a second, non-current employment (allowed, since only one CURRENT is limited)
    second = dict(
        BASE_EMPLOYMENT,
        employer_name="Other Corp",
        start_date="2015-01-01",
        end_date="2016-12-31",
        is_current=False,
    )
    second_resp = await client.post("/api/v1/career-dna/employments", json=second, headers=headers)
    second_id = second_resp.json()["id"]

    # promoting the second (non-current) employment tries to create a new
    # is_current=True row while the first employment is still primary/current
    resp = await client.post(
        f"/api/v1/career-dna/employments/{second_id}/promote",
        json={"new_role_title": "New Title", "effective_date": "2021-01-01"},
        headers=headers,
    )
    assert resp.status_code == 409


async def test_update_employment_not_found(client):
    headers = await _person_headers(client)
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.patch(
        f"/api/v1/career-dna/employments/{fake_id}", json={"description": "x"}, headers=headers
    )
    assert resp.status_code == 404


async def test_delete_employment_not_found(client):
    headers = await _person_headers(client)
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.delete(f"/api/v1/career-dna/employments/{fake_id}", headers=headers)
    assert resp.status_code == 404


async def test_list_employments_filtered_by_is_current(client):
    headers = await _person_headers(client)
    await client.post("/api/v1/career-dna/employments", json=BASE_EMPLOYMENT, headers=headers)
    past = dict(
        BASE_EMPLOYMENT, employer_name="Old Corp", start_date="2015-01-01", end_date="2018-01-01", is_current=False
    )
    await client.post("/api/v1/career-dna/employments", json=past, headers=headers)

    current_only = await client.get("/api/v1/career-dna/employments?is_current=true", headers=headers)
    assert current_only.json()["total"] == 1

    past_only = await client.get("/api/v1/career-dna/employments?is_current=false", headers=headers)
    assert past_only.json()["total"] == 1


async def test_employment_scoped_to_owning_person(client):
    headers_a = await _person_headers(client, email="empA@example.com")
    headers_b = await _person_headers(client, email="empB@example.com")

    created = await client.post("/api/v1/career-dna/employments", json=BASE_EMPLOYMENT, headers=headers_a)
    employment_id = created.json()["id"]

    # user B must not be able to read user A's employment record
    resp = await client.get(f"/api/v1/career-dna/employments/{employment_id}", headers=headers_b)
    assert resp.status_code == 404
