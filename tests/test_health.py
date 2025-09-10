import pytest
from fastapi.testclient import TestClient
from fitbot.app import app


def test_health_endpoint():
    client = TestClient(app)
    r = client.get('/health')
    assert r.status_code == 200
    data = r.json()
    assert 'status' in data

