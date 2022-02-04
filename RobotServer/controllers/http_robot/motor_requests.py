def apply_motor_requests(request_motors_data: dict, device_map, motor_requests: dict) -> None:
    for request_motor_values in request_motors_data:
        request_motor_id = request_motor_values.get("id")
        motor = device_map["Motors"].get(request_motor_id)
        if motor:
            motor_requests[request_motor_id] = request_motor_values
        else:
            raise Exception(f"No motor named {request_motor_id} found")