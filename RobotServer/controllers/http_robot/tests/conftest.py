import collections
import pytest

FlaskApp = collections.namedtuple(
    "FlaskApp", ["test_client", "device_map", "motor_requests", "line_map"]
)


@pytest.fixture
def test_app():
    from http_robot import create_app

    motor_requests = {}
    line_map = {}
    device_map = {}
    app = create_app(
        device_map=device_map, motor_requests=motor_requests, line_map=line_map
    )
    with app.test_client() as test_client:
        yield FlaskApp(
            test_client=test_client,
            device_map=device_map,
            motor_requests=motor_requests,
            line_map=line_map,
        )
