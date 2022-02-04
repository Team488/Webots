import time
import sys
import traceback


def start_zmq(port: int, robotId: str, public_ip: str, device_map: dict):

    zmq_video_sleep_seconds = 1 / 60
    zmq_port_offset = 10
    zmq_port = port + zmq_port_offset
    print(
        f"[HttpRobot{robotId}] Starting zmq server on tcp://{public_ip}:{zmq_port}",
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
