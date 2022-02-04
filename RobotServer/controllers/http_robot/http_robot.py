from typing import List
import logging
import socket
import sys
import threading
import time

from controller import Supervisor

from robot.device_map import build_device_map
from robot.motor_requests import update_motors
from camera_stream import start_zmq
from flask_app import start_flask

# flask log level
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)


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
        target=lambda: start_flask(
            device_map, motor_requests, robot, robotId, get_public_ip(), port
        )
    ).start()
    threading.Thread(
        target=lambda: start_zmq(port, robotId, get_public_ip(), device_map)
    ).start()

    # Run the simulation loop
    print("Starting null op simulation loop")
    while robot.step(timestep) != -1:
        # motor updates need to happen every tick so things like raw torques are constantly applied
        update_motors(device_map, motor_requests)
        # the sleep creates space for the webserver to run more responsively
        time.sleep(timestep / 1000)
    print("Finished")
