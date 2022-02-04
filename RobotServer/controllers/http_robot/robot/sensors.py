import math
import itertools
from itertools import zip_longest

from robot.device_map import get_device_id


def get_world_pose(robot) -> dict:
    # simulation time is reported in seconds
    time = robot.getTime()

    # return exact robot world pose for debugging
    robot_node = robot.getSelf()
    position = robot_node.getPosition()
    rotation = robot_node.getOrientation()
    yaw = math.degrees(math.atan2(rotation[0], rotation[1])) % 360

    return {"Position": 0, "Yaw": 0, "Time": time}


def get_sensors_data(device_map, robot) -> list:
    distance_sensor_values = [
        {
            "ID": get_device_id(distance_sensor),
            "Payload": {"Distance": distance_sensor.getValue()},
        }
        for distance_sensor in device_map["DistanceSensors"].values()
    ]

    bumper_touch_sensor_values = [
        {
            "ID": get_device_id(bumper_touch_sensor_values),
            "Payload": {"Triggered": bumper_touch_sensor_values.getValue() == 1},
        }
        for bumper_touch_sensor_values in device_map["BumperTouchSensors"].values()
    ]

    position_sensor_values = [
        {
            "ID": get_device_id(position_sensor),
            "Payload": {"EncoderTicks": position_sensor.getValue()},
        }
        for position_sensor in device_map["PositionSensors"].values()
    ]

    position_sensor_limit_switch_values = []
    for position_sensor_limit_switch in device_map[
        "PositionSensorLimitSwitch"
    ].values():
        proto_node = robot.getFromDevice(position_sensor_limit_switch)
        limits_field = proto_node.getField("limits")
        position_sensor_name = proto_node.getField("name").getSFString()
        sensor_names_field = proto_node.getField("sensorNames")
        limit_width = proto_node.getField("limitWidth").getSFFloat()
        if limits_field.getCount() != sensor_names_field.getCount():
            print(f"Ignoring misconfigured sensor {position_sensor_name}")
            continue
        for limit_switch_index in range(limits_field.getCount()):
            sensor_name = sensor_names_field.getMFString(limit_switch_index)
            sensor_limit = limits_field.getMFFloat(limit_switch_index)
            position_sensor_limit_switch_values.append(
                {
                    "ID": sensor_name.split("#")[
                        0
                    ].strip(),  # get_device_id only works for real devices
                    "Payload": {
                        "Triggered": position_sensor_limit_switch.getValue()
                        > sensor_limit - limit_width / 2
                        and position_sensor_limit_switch.getValue()
                        < sensor_limit + limit_width / 2
                    },
                }
            )

    imu_sensor_values = [
        {
            "ID": get_device_id(imu),
            "Payload": {
                "Roll": imu.getRollPitchYaw()[2],
                "Pitch": imu.getRollPitchYaw()[1],
                "Yaw": imu.getRollPitchYaw()[0],
                "YawVelocity": gyro.getValues()[2],
            },
        }
        for imu, gyro in zip_longest(
            device_map["IMUs"].values(), device_map["Gyros"].values()
        )
    ]

    return list(
        itertools.chain(
            distance_sensor_values,
            bumper_touch_sensor_values,
            position_sensor_values,
            position_sensor_limit_switch_values,
            imu_sensor_values,
        )
    )
