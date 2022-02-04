from typing import List
from collections import defaultdict
from controller import Node, Supervisor, TouchSensor
from flask import Flask, request

import enum
import itertools
import json
import logging
import math
import socket
import sys
import threading
import time
import traceback

from motor_requests import apply_motor_requests
from sensors import get_sensors_data


# flask log level
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)


class MotorModes(enum.Enum):
    POWER = 0
    VELOCITY = 1
    POSITION = 2


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

        # # return exact robot world pose for debugging
        # robot_node = robot.getSelf()
        # position = robot_node.getPosition()
        # rotation = robot_node.getOrientation()
        # yaw = math.degrees(math.atan2(rotation[0], rotation[1])) % 360

        # simulation time is reported in seconds
        time = robot.getTime()
        return json.dumps(
            {
                "Sensors": sensor_data,
                # "WorldPose": {"Position": position, "Yaw": yaw, "Time": time},
                # Some static fake data to not break the api
                "WorldPose": {"Position": 0, "Yaw": 0, "Time": time},
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

        draw_line(name, point_1, point_2, color_rgb=color_rgb)

        return "OK"

    @app.route("/overlay/arrow", methods=["PUT"])
    def put_arrow():
        request_data = request.json or {}

        name = request_data["name"]
        point_1 = request_data["point_1"]
        point_2 = request_data["point_2"]
        color_rgb = request_data.get("color", [0, 1, 1])

        draw_arrow(name, point_1, point_2, color_rgb=color_rgb)

        return "OK"

    @app.route("/overlay/circle", methods=["PUT"])
    def put_circle():
        request_data = request.json or {}

        name = request_data["name"]
        center = request_data["center"]
        radius = request_data["radius"]
        color_rgb = request_data.get("color", [0, 1, 1])

        draw_circle(name=name, center=center, color_rgb=color_rgb, radius=radius)

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


# Draws a line between point_1 and point_2
# name creates the node in the tree so we just update the same node each time
def draw_line(
    name: str, point_1: List[float], point_2: List[float], color_rgb: List[float]
):
    # Create node with name if it doesn't exist yet
    node_name = f"LINE_{name}"

    if node_name not in line_map:
        root_node = robot.getRoot()
        root_children_field = root_node.getField("children")

        template = (
            f"DEF {node_name} "
            + """Shape {
            appearance Appearance {
                material Material {
                    emissiveColor """
            + " ".join(map(str, color_rgb))
            + """
                }
            }
            geometry DEF TRAIL_LINE_SET IndexedLineSet {
                coord Coordinate {
                    point [
                        0 0 0
                        0 0 0
                    ]
                }
                coordIndex [
                    0 1 -1
                ]
            }
        }"""
        )
        root_children_field.importMFNodeFromString(-1, template)

        # Update the coords based on points
        trail_set_node = robot.getFromDef(f"{node_name}.TRAIL_LINE_SET")
        coordinates_node = trail_set_node.getField("coord").getSFNode()
        point_field = coordinates_node.getField("point")
        line_map[node_name] = point_field
    else:
        point_field = line_map[node_name]

    point_field.setMFVec3f(0, point_1)
    point_field.setMFVec3f(1, point_2)


# Draws a line between point_1 and point_2
# name creates the node in the tree so we just update the same node each time
def draw_arrow(
    name: str,
    point_1: List[float],
    point_2: List[float],
    color_rgb: List[float],
    arrow_angle_deg=35,
    arrow_len_ratio=0.25,
):
    # Create node with name if it doesn't exist yet
    node_name = f"ARROW_{name}"

    if node_name not in line_map:
        root_node = robot.getRoot()
        root_children_field = root_node.getField("children")

        template = (
            f"DEF {node_name} "
            + """Shape {
            appearance Appearance {
                material Material {
                    emissiveColor """
            + " ".join(map(str, color_rgb))
            + """
                }
            }
            geometry DEF TRAIL_LINE_SET IndexedLineSet {
                coord Coordinate {
                    point [
                        0 0 0
                        0 0 0
                        0 0 0
                        0 0 0
                    ]
                }
                coordIndex [
                    0 1 -1
                    1 2 -1
                    1 3 -1
                ]
            }
        }"""
        )
        root_children_field.importMFNodeFromString(-1, template)

        # Update the coords based on points
        trail_set_node = robot.getFromDef(f"{node_name}.TRAIL_LINE_SET")
        coordinates_node = trail_set_node.getField("coord").getSFNode()
        point_field = coordinates_node.getField("point")
        line_map[node_name] = point_field
    else:
        point_field = line_map[node_name]

    # calculate arrow points based on start/end
    # convert to polar
    delta = [point_1[0] - point_2[0], point_1[1] - point_2[1]]
    length = math.sqrt(delta[0] ** 2 + delta[1] ** 2)
    angle = math.atan2(delta[0], delta[1])

    left_angle = angle + math.radians(arrow_angle_deg)
    right_angle = angle - math.radians(arrow_angle_deg)

    arrow_length = length * arrow_len_ratio
    arrow_left = [
        arrow_length * math.sin(left_angle) + point_2[0],
        arrow_length * math.cos(left_angle) + point_2[1],
        point_2[2],
    ]
    arrow_right = [
        arrow_length * math.sin(right_angle) + point_2[0],
        arrow_length * math.cos(right_angle) + point_2[1],
        point_2[2],
    ]

    point_field.setMFVec3f(0, point_1)
    point_field.setMFVec3f(1, point_2)
    point_field.setMFVec3f(2, arrow_left)
    point_field.setMFVec3f(3, arrow_right)


def draw_circle(
    name: str,
    center: List[float],
    color_rgb: List[float],
    radius: float,
    num_segments=20,
):
    # Create node with name if it doesn't exist yet
    node_name = f"CIRCLE_{name}"

    if node_name not in line_map:
        node = robot.getFromDef(node_name)
        root_node = robot.getRoot()
        root_children_field = root_node.getField("children")

        template = (
            f"DEF {node_name} "
            + """Shape {
            appearance Appearance {
                material Material {
                    emissiveColor """
            + " ".join(map(str, color_rgb))
            + """
                }
            }
            geometry DEF TRAIL_LINE_SET IndexedLineSet {
                coord Coordinate {
                    point [
                        """
            + ("0 0 0\n" * num_segments)
            + """
                    ]
                }
                coordIndex [
                    """
            + " ".join(map(str, range(num_segments)))
            + """ 0 -1
                ]
            }
        }"""
        )
        root_children_field.importMFNodeFromString(-1, template)
        node = robot.getFromDef(node_name)

        # Update the coords based on points
        trail_set_node = robot.getFromDef(f"{node_name}.TRAIL_LINE_SET")
        coordinates_node = trail_set_node.getField("coord").getSFNode()
        point_field = coordinates_node.getField("point")
        line_map[node_name] = point_field
    else:
        point_field = line_map[node_name]

    # Use polar coordinates to find points on the circle
    for i in range(num_segments):
        theta = math.pi * 2 / num_segments * i
        point = [
            center[0] + radius * math.cos(theta),
            center[1] + radius * math.sin(theta),
            center[2],
        ]
        point_field.setMFVec3f(i, point)


def update_motors(device_map, motor_requests):
    for motor_id, request_motor_values in motor_requests.items():
        motor = device_map["Motors"][motor_id]
        value = request_motor_values.get("val")
        mode = MotorModes[request_motor_values.get("mode", "velocity").upper()]
        if mode == MotorModes.VELOCITY:
            # this is required to renable velocity PID in case we were last on a different mode. A fancier version would latch
            # on changes to the mode and only set it then.
            motor.setPosition(float("inf"))
            motor.setVelocity(float(value * motor.getMaxVelocity()))
        elif mode == MotorModes.POSITION:
            motor.setPosition(float(value))
        elif mode == MotorModes.POWER:
            motor.setForce(float(value * motor.getMaxTorque()))
        else:
            raise Exception(f"Unhandled motor mode {mode}")


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


def start_zmq():
    global device_map, port

    zmq_video_sleep_seconds = 1 / 60
    zmq_port_offset = 10
    zmq_port = port + zmq_port_offset
    print(
        f"[HttpRobot{robotId}] Starting zmq server on tcp://{get_public_ip()}:{zmq_port}",
        flush=True,
    )

    try:
        import zmq

        # Start a ZeroMQ server.
        zmq_context = zmq.Context()
        zmq_socket = zmq_context.socket(zmq.PUB)
        zmq_socket.bind(f"tcp://0.0.0.0:{zmq_port}")

        # Get the camera, and define a message template to send the image.
        if not device_map["Cameras"]:
            print("No camera found, skipping zmq setup")
            return
        camera = next(iter(device_map["Cameras"].values()))
        camera_depth = 4
        message = [
            b"image",
            camera.getHeight().to_bytes(4, byteorder="big"),
            camera.getWidth().to_bytes(4, byteorder="big"),
            camera_depth.to_bytes(4, byteorder="big"),
            None,
        ]

        while True:
            # Get the camera image and send the full message.
            message[-1] = bytes(camera.getImage())
            zmq_socket.send_multipart(message)

            # Sleep so we don't overload the ZMQ socket.
            # The sleep time is correlated with framerate, but doesn't seem to match it exactly.
            time.sleep(zmq_video_sleep_seconds)

    except:
        print("Could not start zmq!", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)


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
    threading.Thread(target=start_zmq).start()

    # Run the simulation loop
    print("Starting null op simulation loop")
    while robot.step(timestep) != -1:
        # motor updates need to happen every tick so things like raw torques are constantly applied
        update_motors(device_map, motor_requests)
        # the sleep creates space for the webserver to run more responsively
        time.sleep(timestep / 1000)
    print("Finished")
