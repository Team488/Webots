from typing import List
import json
import logging
import math
import socket
import sys
import threading
import time
import traceback

from controller import Supervisor
from flask import Flask, request

from robot.device_map import build_device_map
from robot.motor_requests import apply_motor_requests, update_motors
from robot.sensors import get_sensors_data, get_world_pose
from webots_draw import draw_line, draw_arrow, draw_circle
from camera_stream import start_zmq

# flask log level
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)


def create_app(device_map, motor_requests, robot):
    app = Flask(__name__)

    @app.route("/ping")
    def ping():
        "Basic Health check"
        return "pong"

    @app.route("/motors", methods=["PUT"])
    def put_motors():
        request_data = request.json
        apply_motor_requests(request_data["motors"], device_map, motor_requests)

        # return sensor data
        sensor_data = get_sensors_data(device_map, robot)

        world_pose = get_world_pose(robot)

        return json.dumps(
            {
                "Sensors": sensor_data,
                # "WorldPose": {"Position": position, "Yaw": yaw, "Time": time},
                # Some static fake data to not break the api
                "WorldPose": world_pose,
            }
        )

    @app.route("/position", methods=["PUT"])
    def reset_position():
        request_data = request.json or {}
        target_position = request_data.get("position", [0, 0, 0.1])
        # defaults to straight up
        target_rotation = request_data.get("rotation", [1, 0, 0, 0])
        print(f"Resetting position to {target_position} @ {target_rotation}")

        robot_node = robot.getSelf()
        translation_field = robot_node.getField("translation")
        rotation_field = robot_node.getField("rotation")

        translation_field.setSFVec3f(target_position)
        rotation_field.setSFRotation(target_rotation)
        robot_node.resetPhysics()

        return "OK"

    @app.route("/overlay/line", methods=["PUT"])
    def put_line():
        request_data = request.json or {}

        name = request_data["name"]
        point_1 = request_data["point_1"]
        point_2 = request_data["point_2"]
        color_rgb = request_data.get("color", [0, 1, 1])

        draw_line(robot, line_map, name, point_1, point_2, color_rgb=color_rgb)

        return "OK"

    @app.route("/overlay/arrow", methods=["PUT"])
    def put_arrow():
        request_data = request.json or {}

        name = request_data["name"]
        point_1 = request_data["point_1"]
        point_2 = request_data["point_2"]
        color_rgb = request_data.get("color", [0, 1, 1])

        draw_arrow(robot, line_map, name, point_1, point_2, color_rgb=color_rgb)

        return "OK"

    @app.route("/overlay/circle", methods=["PUT"])
    def put_circle():
        request_data = request.json or {}

        name = request_data["name"]
        center = request_data["center"]
        radius = request_data["radius"]
        color_rgb = request_data.get("color", [0, 1, 1])

        draw_circle(
            robot,
            line_map,
            name=name,
            center=center,
            color_rgb=color_rgb,
            radius=radius,
        )

        return "OK"

    return app


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
        return "127.0.0.1"


def start_flask(device_map, motor_requests, robot):

    flask_app = create_app(
        device_map=device_map, motor_requests=motor_requests, robot=robot
    )

    print(
        f"[HttpRobot{robotId}] Starting flask server on http://{get_public_ip()}:{port}",
        flush=True,
    )

    # Set the host to allow remote connections
    flask_app.run(host="0.0.0.0", port=port)




if __name__ == "__main__":
    # TODO: use argparse to clean this up
    robotId = int(sys.argv[1])
    port = int(sys.argv[2])
    # Create the robot
    robot = Supervisor()
    timestep = int(robot.getBasicTimeStep())
    device_map = build_device_map(robot, timestep)
    motor_requests = {}
    line_map = {}
    threading.Thread(
        target=lambda: start_flask(device_map, motor_requests, robot)
    ).start()
    threading.Thread(target=lambda: start_zmq(port, robotId, get_public_ip(), device_map)).start()

    # Run the simulation loop
    print("Starting null op simulation loop")
    while robot.step(timestep) != -1:
        # motor updates need to happen every tick so things like raw torques are constantly applied
        update_motors(device_map, motor_requests)
        # the sleep creates space for the webserver to run more responsively
        time.sleep(timestep / 1000)
    print("Finished")
