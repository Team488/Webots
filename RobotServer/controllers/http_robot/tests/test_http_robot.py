from http_robot import create_app


def test_ping():
    flask_app = create_app()

    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as test_client:
        response = test_client.get("/ping")

        assert response.status_code == 200
        assert b"pong" in response.data
