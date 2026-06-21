from flask.testing import FlaskClient


def test_health_check_returns_ok(client: FlaskClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_unknown_route_returns_consistent_error(client: FlaskClient) -> None:
    response = client.get("/does-not-exist")
    body = response.get_json()

    assert response.status_code == 404
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
