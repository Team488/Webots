import collections
from unittest.mock import Mock, MagicMock
import pytest

FlaskApp = collections.namedtuple(
    "FlaskApp", ["test_client", "device_map", "motor_requests", "mock_robot"]
)


@pytest.fixture
def test_app():
    from http_robot import create_app

    motor_requests = {}
    device_map = collections.defaultdict(dict)
    robot = MagicMock()
    robot.getSelf.getOrientation.return_value = [0, 0]
    app = create_app(device_map=device_map, motor_requests=motor_requests, robot=robot)
    with app.test_client() as test_client:
        yield FlaskApp(
            test_client=test_client,
            device_map=device_map,
            motor_requests=motor_requests,
            mock_robot=robot,
        )
