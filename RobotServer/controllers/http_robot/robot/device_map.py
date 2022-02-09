from collections import defaultdict

from controller import Node, TouchSensor


def get_device_id(device) -> str:
    return device.getName().split("#")[0].strip()


def build_device_map(robot, timestep) -> dict:
    device_map = defaultdict(dict)

    device_count = robot.getNumberOfDevices()
    print(f"Found {device_count} devices on robot")
    for i in range(device_count):
        device = robot.getDeviceByIndex(i)
        device_type = device.getNodeType()
        device_id = get_device_id(device)

        if device_type == Node.ROTATIONAL_MOTOR or device_type == Node.LINEAR_MOTOR:
            # Initialize the motor with an infinite target position so that we can directly control velocity
            device.setPosition(float("inf"))
            device.setVelocity(0)
            device_map["Motors"][device_id] = device
        elif device_type == Node.DISTANCE_SENSOR:
            # Initialize the distance sensor with an update frequency
            device.enable(timestep)
            device_map["DistanceSensors"][device_id] = device
        elif (
            device_type == Node.TOUCH_SENSOR and device.getType() == TouchSensor.BUMPER
        ):
            device.enable(timestep)
            device_map["BumperTouchSensor"][device_id] = device
        elif device_type == Node.POSITION_SENSOR:
            device.enable(timestep)
            device_map["PositionSensors"][device_id] = device
            # Handle PositionSensorLimitSwitch
            device_node = robot.getFromDevice(device)
            if (
                device_node
                and device_node.isProto()
                and device_node.getTypeName() == "PositionSensorLimitSwitch"
            ):
                device_map["PositionSensorLimitSwitch"][device_id] = device
        elif device_type == Node.INERTIAL_UNIT:
            device.enable(timestep)
            device_map["IMUs"][device_id] = device
        elif device_type == Node.CAMERA:
            device.enable(timestep)
            device_map["Cameras"][device_id] = device
        elif device_type == Node.GYRO:
            device.enable(timestep)
            device_map["Gyros"][device_id] = device
        elif device_type == Node.RANGE_FINDER:
            device.enable(timestep)
            device_map["RangeFinders"][device_id] = device
        else:
            print(
                f"Found unknown device of type {device_type} with ID {device_id} not mapped"
            )

    return device_map
