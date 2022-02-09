import time
import sys
import traceback
import enum

from controller import Node

from robot.device_map import get_device_id

# See for these values: https://docs.opencv.org/4.5.5/d1/d1b/group__core__hal__interface.html
class OpenCVDepth(enum.Enum):
    U8 = 0
    U16 = 2

# These are simply the number stored as a single bytes.
class OpenCVChannel(enum.Enum):
    One = 1
    Four = 4


def start_zmq(port: int, robotId: str, public_ip: str, device_map: dict):

    zmq_video_sleep_seconds = 1 / 60
    zmq_port_offset = 10
    zmq_port = port + zmq_port_offset

    try:
        import zmq
        import numpy as np

        # Start a ZeroMQ server.
        zmq_context = zmq.Context()
        zmq_socket = zmq_context.socket(zmq.PUB)
        zmq_socket.bind(f"tcp://0.0.0.0:{zmq_port}")

        # Create an message template for each device of the format:
        # [ topic, height, width, bit_depth, channel_count, image_data ]
        camera_devices = list(device_map["Cameras"].values())
        camera_devices.extend(device_map["RangeFinders"].values())
        messages = {
            get_device_id(device): [
                get_device_id(device).encode('ascii'),  # The first element of a multipart message is also considered the "topic" name.
                device.getHeight().to_bytes(4, byteorder='little'),
                device.getWidth().to_bytes(4, byteorder='little'),
                (OpenCVDepth.U16 if device.getNodeType() == Node.RANGE_FINDER else OpenCVDepth.U8).value.to_bytes(1, byteorder='little'),
                (OpenCVChannel.One if device.getNodeType() == Node.RANGE_FINDER else OpenCVChannel.Four).value.to_bytes(1, byteorder='little'),
                None  # Reserve a placeholder for the image buffer.
            ] for device in camera_devices
        }

        # Print the ZMQ URLs with topics as paths. Note that this is a custom format. In practice, the URLs and topics are used independently.
        for message in messages.values():
            print(f"[HttpRobot{robotId}] Starting zmq server on tcp://{public_ip}:{zmq_port}/{message[0].decode()}", flush=True)

        while True:
            for device in camera_devices:

                # Start with the message template.
                message = messages[get_device_id(device)]

                # Set the image in the message depending on the type of device.
                device_type = device.getNodeType()
                if device_type == Node.CAMERA:
                    message[-1] = bytes(device.getImage())
                elif device_type == Node.RANGE_FINDER:
                    # RangeFinder images are received from Webots as single-channel float32 images at meter-scale.
                    # We stream them as single-channel uint16 images at millimeter-scale, to match the more common Realsense format.
                    float_buffer = np.frombuffer(device.getRangeImage(data_type = 'buffer'), dtype=np.float32)
                    message[-1] = (float_buffer * 1000).astype('uint16').tobytes()

                # Send the full message.
                zmq_socket.send_multipart(message)

            # Sleep so we don't overload the ZMQ socket.
            # The sleep time is correlated with framerate, but doesn't seem to match it exactly.
            time.sleep(zmq_video_sleep_seconds)

    except:
        print("Could not start zmq!", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
