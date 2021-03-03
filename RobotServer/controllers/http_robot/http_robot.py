from collections import defaultdict
from controller import Node, Supervisor
from flask import Flask, request
import itertools
import json
import logging
import math
import socket
import sys
import threading
import time
import traceback

# TODO: use argparse to clean this up
robotId = int(sys.argv[1])
port = int(sys.argv[2])

app = Flask(__name__)

# flask log level
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def get_device_id(device):
    return device.getName().split("#")[0].strip()

def get_public_ip():
    try:
        # In case there are multiple network interfaces,
        # get the public IP address by connecting to Google.
        probe_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe_socket.connect(("8.8.8.8", 80))
        ip = probe_socket.getsockname()[0]
        probe_socket.close()
        return ip
    except:
        return '127.0.0.1'

@app.route("/ping")
def ping():
    "Basic Health check"
    return "pong"

@app.route("/motors", methods=['PUT'])
def put_motors():
    global device_map
    request_data = request.json
    for request_motor_values in request_data['motors']:
        request_motor_id = request_motor_values.get("id")
        motor = device_map["Motors"].get(request_motor_id)
        if motor:
            # TODO: handle other modes of setting motor output
            throttle_percent = request_motor_values.get("val")
            if throttle_percent is not None:
                motor.setVelocity(float(throttle_percent * motor.getMaxVelocity()))
        else:
            raise Exception(f"No motor named {request_motor_id} found")

    # return sensor data

    distance_sensor_values = [{
            "ID": get_device_id(distance_sensor),
            "Payload": {
                "Distance": distance_sensor.getValue()
            }
        }
        for distance_sensor in device_map["DistanceSensors"].values()
    ]

    position_sensor_values = [{
            "ID": get_device_id(position_sensor),
            "Payload": {
                "EncoderTicks": position_sensor.getValue()
            }
        }
        for position_sensor in device_map["PositionSensors"].values()
    ]

    imu_sensor_values =  [{
            "ID": get_device_id(imu),
            "Payload": {
                "Roll": imu.getRollPitchYaw()[2],
                "Pitch": imu.getRollPitchYaw()[1],
                "Yaw": imu.getRollPitchYaw()[0],
            }
        }
        for imu in device_map["IMUs"].values()
    ]

    # return exact robot world pose for debugging
    robot_node = robot.getSelf()
    position = robot_node.getPosition()
    rotation = robot_node.getOrientation()
    yaw = math.degrees(math.atan2(rotation[0], rotation[1])) % 360
    # simulation time is reported in seconds
    time = robot.getTime()
    return json.dumps({
        "Sensors": list(itertools.chain(
            distance_sensor_values,
            position_sensor_values,
            imu_sensor_values
        )),
        "WorldPose": {
            "Position": position,
            "Yaw": yaw,
            "Time": time
        }
    })

@app.route("/position", methods=['PUT'])
def reset_position():
    requestData = request.json or {}
    target_position = requestData.get("position", [0,0,0.1])
    # defaults to straight up
    target_rotation = requestData.get("rotation", [1, 0, 0, 0]) 
    print(f"Resetting position to {target_position} @ {target_rotation}")

    robot_node = robot.getSelf()
    translation_field = robot_node.getField("translation")
    rotation_field = robot_node.getField("rotation")

    translation_field.setSFVec3f(target_position)
    rotation_field.setSFRotation(target_rotation)
    robot_node.resetPhysics()

    return 'OK'
    
def build_device_map(robot):
    device_map = defaultdict(dict)

    device_count = robot.getNumberOfDevices()
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
        elif device_type == Node.POSITION_SENSOR:
            device.enable(timestep)
            device_map["PositionSensors"][device_id] = device
        elif device_type == Node.INERTIAL_UNIT:
            device.enable(timestep)
            device_map["IMUs"][device_id] = device
        elif device_type == Node.CAMERA:
            device.enable(timestep)
            device_map["Cameras"][device_id] = device

    return device_map

def start_flask():
    global app, port

    print(f"[HttpRobot{robotId}] Starting flask server on http://{get_public_ip()}:{port}", flush=True)

    # Set the host to allow remote connections
    app.run(host='0.0.0.0', port=port)

def start_zmq():
    global device_map, port

    zmq_video_sleep_seconds = 1 / 60
    zmq_port_offset = 10
    zmq_port = port + zmq_port_offset
    print(f"[HttpRobot{robotId}] Starting zmq server on tcp://{get_public_ip()}:{zmq_port}", flush=True)

    try:
        import cv2
        import numpy as np
        import zmq

        camera = next(iter(device_map["Cameras"].values()))
        image_height = camera.getHeight().to_bytes(4, byteorder='big')
        image_width = camera.getWidth().to_bytes(4, byteorder='big')
        image_depth = (4).to_bytes(4, byteorder='big')

        zmq_context = zmq.Context()
        zmq_socket = zmq_context.socket(zmq.PUB)
        zmq_socket.bind(f"tcp://0.0.0.0:{zmq_port}")

        while True:
            image_data = bytes(camera.getImage())
            zmq_socket.send_multipart([b"image", image_height, image_width, image_depth, image_data])
            
            # Sleep so we don't overload the ZMQ socket.
            # The sleep time is correlated with framerate, but doens't seem to match it exactly.
            time.sleep(zmq_video_sleep_seconds)

    except:
        print("Could not start zmq!", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)

if __name__ == "__main__":
    # Create the robot
    robot = Supervisor()
    timestep = int(robot.getBasicTimeStep())
    device_map = build_device_map(robot)
    threading.Thread(target=start_flask).start()
    threading.Thread(target=start_zmq).start()

    # Run the simulation loop
    print("Starting null op simulation loop")
    while robot.step(timestep) != -1:
        time.sleep(timestep / 1000)
    print("Finished")
