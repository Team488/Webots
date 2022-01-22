"""swerve_test controller."""

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor
from controller import Robot

# create the Robot instance.
robot = Robot()

# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())

# You should insert a getDevice-like function in order to get the
# instance of a device of the robot. Something like:
wheels = ["fl", "fr", "bl", "br"]
wheel_motors = [robot.getDevice(f'wheel_motor_{wheel}') for wheel in wheels]
direction_motors = [robot.getDevice(f'direction_motor_{wheel}') for wheel in wheels]

for wheel_motor in wheel_motors:
    wheel_motor.setPosition(float('inf'))
    wheel_motor.setVelocity(0.1)
for direction_motor in direction_motors:
    pass
    #direction_motor.setPosition(float('inf'))
    #direction_motor.setVelocity(0.1)

#  ds = robot.getDevice('dsname')
#  ds.enable(timestep)

# Main loop:
# - perform simulation steps until Webots is stopping the controller
while robot.step(timestep) != -1:
    # Read the sensors:
    # Enter here functions to read sensor data, like:
    #  val = ds.getValue()

    # Process sensor data here.

    # Enter here functions to send actuator commands, like:
    #  motor.setPosition(10.0)
    pass

# Enter here exit cleanup code.
