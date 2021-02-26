import cv2
import numpy as np
import time
import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect('tcp://127.0.0.1:10012')
socket.subscribe('image')

num_frames = 0
start_time = time.time()
while True:
    try:
        frame = socket.recv_multipart()
        image_height = int.from_bytes(frame[1], byteorder='big')
        image_width = int.from_bytes(frame[2], byteorder='big')
        image_depth = int.from_bytes(frame[3], byteorder='big')
        image_data = frame[4]

        image = np.frombuffer(image_data, np.uint8).reshape((image_height, image_width, image_depth))

        cv2.imshow('image', image)
        cv2.waitKey(1)

        num_frames += 1
        curr_time = time.time()
        print(num_frames / (curr_time - start_time))

    except:
        cv2.destroyAllWindows()
        break
