
import init
import melvin
import utility

def mappingwide():
    """
    Scan the map with wide lens to create a reference used to recognize unknown objectives

    """
    init.wide_scanx += 1
    if init.wide_scanx <= 23:
        init.requests.put(init.url + "control", json={"state": 'active', "camera_angle": 'wide', "vel_x": 70, "vel_y": 0})
        init.time.sleep(1)
        response_img = init.requests.get(init.url + "image").content
        data = init.json.loads(response_obs = init.requests.get(init.url + "observation").content)
        utility.take_photo(response_img, data['telemetry']['angle'], data['telemetry']['x'], data['telemetry']['y'],mapwide= True)
        init.requests.put(init.url + "control", json={"state": 'charge', "camera_angle": 'wide', "vel_x": 70, "vel_y": 0})
        return
    if init.wide_scanx == 24:
        init.requests.put(init.url + "control", json={"state": 'active', "camera_angle": 'wide', "vel_x": 70, "vel_y": 10})
        init.time.sleep(22)
        init.requests.put(init.url + "control", json={"state": 'charge', "camera_angle": 'wide', "vel_x": 70, "vel_y": 10})
        init.time.sleep(74)
        init.requests.put(init.url + "control", json={"state": 'active', "camera_angle": 'wide', "vel_x": 70, "vel_y": 0})
        init.time.sleep(22)
        init.requests.put(init.url + "control", json={"state": 'charge', "camera_angle": 'wide', "vel_x": 70, "vel_y": 0})
        init.wide_scanx = 0
        return
    return
