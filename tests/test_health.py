from fastapi.testclient import TestClient
from app.app import app

client = TestClient(app)

def test_health():
    """Test that the `/health` endpoint returns HTTP 200 with a status of 'ok'."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
