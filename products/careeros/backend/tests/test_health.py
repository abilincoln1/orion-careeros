import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "service" in body and "version" in body


@pytest.mark.asyncio
async def test_liveness(client):
    resp = await client.get("/api/v1/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness(client):
    resp = await client.get("/api/v1/health/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "operational"
