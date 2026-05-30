from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_analyze_invalid_strictness():
    response = client.post("/analyze", json={
        "code_snippet": "x=1",
        "language": "python",
        "strictness_level": 99
    })
    assert response.status_code == 422

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "200 OK"}

def test_analyze_invalid_strictness():
    response = client.post("/analyze", json={
        "code_snippet": "x=1",
        "language": "python",
        "strictness_level": 99
    })
    assert response.status_code == 422

def test_agent_empty_input():
    response = client.post("/agent", json={
        "code_snippet": ""
    })
    assert response.status_code == 400