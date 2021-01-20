import threading               
import sys                             
import logging
import time
import json

from flask import Flask, request       
from controller import Node, Robot

app = Flask(__name__)

# flask log level
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def getDeviceId(device):
    return device.getName().split("#")[0].strip()

@app.route("/ping")
def ping():
    "Basic Health check"
    return "pong"

@app.route("/motors", methods=['PUT'])
def putMotors():
    global deviceMap
    requestData = request.json
    for requestMotorValues in requestData['motors']:
        requestMotorId = requestMotorValues.get("id")
        if requestMotorId in deviceMap["Motors"]:
            motor = deviceMap["Motors"].get(requestMotorId)
            # TODO: handle other modes of setting motor output
            throttlePercent = requestMotorValues.get("val")
            if throttlePercent:
                motor.setVelocity(float(throttlePercent * motor.getMaxVelocity()))
        else:
            raise Exception(f"No motor named {motor_id} found")

    # return sensor data
    return json.dumps({
        "Sensors": [
            {
                "ID": getDeviceId(distanceSensor),
                "Payload": {
                    "Distance": distanceSensor.getValue()
                }
            }
            for distanceSensor in deviceMap["DistanceSensors"].values()
        ]
    })
    
def buildDeviceMap(robot):
    deviceMap = {
        "Motors": {},
        "DistanceSensors": {}
    }

    deviceCount = robot.getNumberOfDevices()
    for i in range(deviceCount):
        device = robot.getDeviceByIndex(i)
        deviceType = device.getNodeType()
        deviceId = getDeviceId(device)
        
        if deviceType == Node.ROTATIONAL_MOTOR:
            # Initialize the motor with an infinite target position so that we can directly control velocity
            device.setPosition(float("inf"))
            device.setVelocity(0)
            deviceMap["Motors"][deviceId] = device

        elif deviceType == Node.DISTANCE_SENSOR:
            # Initialize the distance sensor with an update frequency
            device.enable(timestep)
            deviceMap["DistanceSensors"][deviceId] = device

    return deviceMap

def startFlask():
    global app
    # TODO: use argparse to clean this up
    port = int(sys.argv[2])
    app.run(port=port)

if __name__ == "__main__":
    # Create the robot
    robot = Robot()
    timestep = int(robot.getBasicTimeStep())

    # If the controller started before the supervisor inserted all of the args,
    # just run an empty simulator loop so we don't block the simulation while
    # we wait for the supervisor to restart this controller
    if sys.argv[-1] != "READY":
        while robot.step(timestep) != -1:
            pass

    print("Starting flask server")
    deviceMap = buildDeviceMap(robot)
    threading.Thread(target=startFlask).start()

    # Run the simulation loop
    print("Starting null op simulation loop")
    while robot.step(timestep) != -1:
        time.sleep(timestep / 1000)
    print("Finished")


