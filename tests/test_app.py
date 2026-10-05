from app import app


def test_health_returns_healthy_status():
    response = app.test_client().get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}
