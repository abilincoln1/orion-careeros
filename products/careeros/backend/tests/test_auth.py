import pytest


@pytest.mark.asyncio
async def test_register_user(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "abi@example.com", "password": "supersecret1", "full_name": "Abiodun Adeniran"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "abi@example.com"
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_register_duplicate_email_rejected(client):
    payload = {"email": "dup@example.com", "password": "supersecret1"}
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_login_success_and_me(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "supersecret1"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "supersecret1"},
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    assert "access_token" in tokens and "refresh_token" in tokens

    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "login@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password_rejected(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpw@example.com", "password": "supersecret1"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpw@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_flow(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@example.com", "password": "supersecret1"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "supersecret1"},
    )
    refresh_token = login_resp.json()["refresh_token"]
    resp = await client.post(
        "/api/v1/auth/refresh",
        params={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()
