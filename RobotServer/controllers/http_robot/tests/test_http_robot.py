import json
from unittest.mock import Mock

from pytest import mark

from flask_app import create_app


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


def test_put_motors__set_position(test_app):
    motor_id = "Motor1"

    test_app.device_map["Motors"][motor_id] = Mock()

    response = test_app.test_client.put(
        "/motors",
        data=json.dumps({"motors": [{"id": motor_id, "value": 1.0, "mode": "position"}]}),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert test_app.motor_requests[motor_id] == {"id": motor_id, "value": 1.0, "mode": "position"}


@mark.parametrize(
    "sensor_type, payload_name, payload_value",
    [
        ("PositionSensors", "EncoderTicks", 100),
        ("BumperTouchSensors", "Triggered", True),
        ("DistanceSensors", "Distance", 100.0),
    ],
)
def test_put_motors__get_basic_sensor(
    sensor_type, payload_name, payload_value, test_app
):
    sensor_id = "CAN1"
    test_app.device_map[sensor_type][sensor_id] = Mock(
        getName=Mock(return_value=sensor_id), getValue=Mock(return_value=payload_value)
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
            "ID": sensor_id,
            "Payload": {payload_name: payload_value},
        }
    ]


def test_put_motors__get_imu(test_app):
    imu_id = "imu_id"
    test_app.device_map["IMUs"][imu_id] = Mock(
        getName=Mock(return_value=imu_id),
        getRollPitchYaw=Mock(return_value=[-0.5, 0.5, 1.5]),
    )
    test_app.device_map["Gyros"]["gyro_id"] = Mock(
        getName=Mock(return_value="gyro_id"),
        getValues=Mock(return_value=[-1.0, 0.1, 1.0]),
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
            "ID": imu_id,
            "Payload": {
                "Roll": 1.5,
                "Pitch": 0.5,
                "Yaw": -0.5,
                "YawVelocity": 1.0,
            },
        }
    ]
