import json
from unittest.mock import Mock

from http_robot import create_app


def test_ping(test_app):
    response = test_app.test_client.get("/ping")

    assert response.status_code == 200
    assert b"pong" in response.data


def test_put_motors__empty_list(test_app):
    response = test_app.test_client.put(
        "/motors", data=json.dumps({"motors": []}), content_type="application/json"
    )

    assert response.status_code == 200


def test_put_motors__invalid_motor(test_app):
    response = test_app.test_client.put(
        "/motors",
        data=json.dumps({"motors": [{"id": "Motor100", "value": 1.0}]}),
        content_type="application/json",
    )

    assert response.status_code == 500


def test_put_motors__default_set(test_app):
    motor_id = "Motor1"

    test_app.device_map["Motors"][motor_id] = Mock()

    response = test_app.test_client.put(
        "/motors",
        data=json.dumps({"motors": [{"id": motor_id, "value": 1.0}]}),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert test_app.motor_requests[motor_id] == {"id": motor_id, "value": 1.0}


def test_put_motors__get_position_sensor(test_app):
    position_sensor_id = "CAN1"
    test_app.device_map["PositionSensors"][position_sensor_id] = Mock(
        getName=Mock(return_value=position_sensor_id), getValue=Mock(return_value=100)
    )

    response = test_app.test_client.put(
        "/motors",
        data=json.dumps({"motors": []}),
        content_type="application/json",
    )

    print(response.get_data(as_text=True))
    response_data = json.loads(response.get_data(as_text=True))

    assert response.status_code == 200
    assert response_data["Sensors"] == [
        {
            "ID": position_sensor_id,
            "Payload": {"EncoderTicks": 100},
        }
    ]
