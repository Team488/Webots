import json
from flask import Flask, request

from robot.motor_requests import apply_motor_requests
from robot.sensors import get_sensors_data, get_world_pose
from webots_draw import draw_line, draw_arrow, draw_circle


def start_flask(
    device_map, motor_requests, robot, robotId: str, public_ip: str, port: int
):

    flask_app = create_app(
        device_map=device_map, motor_requests=motor_requests, robot=robot
    )

    print(
        f"[HttpRobot{robotId}] Starting flask server on http://{public_ip}:{port}",
        flush=True,
    )

    # Set the host to allow remote connections
    flask_app.run(host="0.0.0.0", port=port)


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
