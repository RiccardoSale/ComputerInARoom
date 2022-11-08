import init
import melvin
import utility


# USARE CON JOB A 57 SECONDI   58 -1 DI SLEEP IN CASO MODIFICARE
# Function that scan the map and saves images
def scan_map():
    init.scanx += 1
    if init.scanx <= 40:
        if init.block is not True:
            init.requests.put(init.url + "control",
                              json={"state": 'active', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
        init.time.sleep(1)
        response_img = init.requests.get(init.url + "image").content
        response_obs = init.requests.get(init.url + "observation").content
            # retrive data from observation for the name of the photo
        data = init.json.loads(response_obs)
        # take photo
        if init.block is not True:
            utility.take_photo(response_img, data['telemetry']['angle'], data['telemetry']['x'], data['telemetry']['y'])
            # change to charge with old parameters
        if init.block is not True:
            init.requests.put(init.url + "control",
                              json={"state": 'charge', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
        return
    if init.scanx == 41:  # STOP JOB ROW COMPLETED #COUNT BIGGER THAN 1
        init.scanx = 0
        init.sched.pause_job('mapping')
        if init.block is not True:
            init.requests.put(init.url + "control",
                          json={"state": 'active', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 1})
        init.time.sleep(586)
        if init.block is not True:
            init.requests.put(init.url + "control",
                          json={"state": 'active', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
        init.sched.resume_job('mapping')
        return
