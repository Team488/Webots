from http_robot import create_app


def test_ping(test_app):
    response = test_app.test_client.get("/ping")

    assert response.status_code == 200
    assert b"pong" in response.data
