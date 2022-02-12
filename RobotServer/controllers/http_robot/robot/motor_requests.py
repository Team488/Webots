import enum


class MotorModes(enum.Enum):
    POWER = 0
    VELOCITY = 1
    POSITION = 2
    VIRTUAL_SOLENOID = 3

class SolenoidPositions(enum.Enum):
    ON = 'on'
    OFF = 'off'


def apply_motor_requests(
    request_motors_data: dict, device_map: dict, motor_requests: dict
) -> None:
    for request_motor_values in request_motors_data:
        request_motor_id = request_motor_values.get("id")
        motor = device_map["Motors"].get(request_motor_id)
        if motor:
            motor_requests[request_motor_id] = request_motor_values
        else:
            raise Exception(f"No motor named {request_motor_id} found")


def update_motors(device_map: dict, motor_requests: dict) -> None:
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
        elif mode == MotorModes.VIRTUAL_SOLENOID:
            target_position = SolenoidPositions[value.upper()]
            # Set the max velocity that the positional pid can use
            motor.setVelocity(motor.getMaxVelocity())
            if target_position == SolenoidPositions.ON:
                motor.setPosition(motor.getMaxPosition())
            elif target_position == SolenoidPositions.OFF:
                motor.setPosition(motor.getMinPosition())
            else:
                raise ValueError("Unknown solenoid position: " + target_position)
        elif mode == MotorModes.POWER:
            motor.setForce(float(value * motor.getMaxTorque()))
        else:
            raise Exception(f"Unhandled motor mode {mode}")
