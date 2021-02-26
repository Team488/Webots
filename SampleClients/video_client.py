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
    frame = socket.recv_multipart()
    image_height = int.from_bytes(frame[1], byteorder='big')
    image_width = int.from_bytes(frame[2], byteorder='big')
    image_depth = int.from_bytes(frame[3], byteorder='big')
    image_data = frame[4]

    image = np.frombuffer(image_data, np.uint8).reshape((image_height, image_width, image_depth))

    image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    image_mask = cv2.inRange(image_hsv, (40,10,0), (70,255,255))
    contours, _ = cv2.findContours(image_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    annotated_image = cv2.drawContours(image, contours, -1, (0,0,255), 2)

    cv2.imshow('image', annotated_image)
    if cv2.waitKey(1) == 27:
        cv2.destroyAllWindows()
        break

    num_frames += 1
    curr_time = time.time()
    print(num_frames / (curr_time - start_time))
