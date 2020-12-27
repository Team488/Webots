import threading               
import sys                             

from flask import Flask         
from controller import Robot    

print("Http robot starting...")

app = Flask(__name__)

@app.route("/ping")
def ping():
    print("ping")
    return "pong"

@app.route("/spin")
def spin():
    print("Trying to spin")
    motorFrontLeft.setVelocity(1.0)
    motorFrontRight.setVelocity(-1.0)
    motorBackLeft.setVelocity(1.0)
    motorBackRight.setVelocity(-1.0)
    return "ack"

@app.route("/")
def main():
    # Send inputs to the robot
    value = requestData.get("vFrontLeft")
    if value != None:
        motorFrontLeft.setVelocity(float(value))
    value = requestData.get("vFrontRight")
    if value != None:
        motorFrontRight.setVelocity(float(value))
    value = requestData.get("vBackLeft")
    if value != None:
        motorBackLeft.setVelocity(float(value))
    value = requestData.get("vBackRight")
    if value != None:
        motorBackRight.setVelocity(float(value))

    return data

# Create the robot
robot = Robot()

# TODO: Maybe find a way to generalize the following motor and sensor initializations.
#       For example, the robot template could have motor and sensor identifiers baked
#       into the controller args. These would be specific to a given robot template
#       and would come before any additional args that the supervisor adds.

# Initialize motors
motorFrontLeft = robot.getMotor("FL motor")
motorFrontRight = robot.getMotor("FR motor")
motorBackLeft = robot.getMotor("BL motor")
motorBackRight = robot.getMotor("BR motor")
motorFrontLeft.setPosition(float("inf"))
motorFrontRight.setPosition(float("inf"))
motorBackLeft.setPosition(float("inf"))
motorBackRight.setPosition(float("inf"))
motorFrontLeft.setVelocity(0.0)
motorFrontRight.setVelocity(0.0)
motorBackLeft.setVelocity(0.0)
motorBackRight.setVelocity(0.0)

def start_flask():
    # TODO: use argparse to clean this up
    port = int(sys.argv[2])
    app.run(port=port)

if __name__ == "__main__":
    # If the controller started before the supervisor inserted all of the args,
    # just run an empty simulator loop so we don't block the simulation while
    # we wait for the supervisor to restart this controller
    if sys.argv[-1] != "READY":
        timestep = int(robot.getBasicTimeStep())
        while robot.step(timestep) != -1:
            pass

    print("Starting flask server")
    threading.Thread(target=start_flask).start()

    # Run the simulation loop
    print("Starting null op simulation loop")
    timestep = int(robot.getBasicTimeStep())
    while robot.step(timestep) != -1:
        pass


