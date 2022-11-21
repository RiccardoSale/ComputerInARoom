import init
import melvin
import utility


OFFSET = 300
RIGHT_BORDER = 21600


def scan_map():
    """
    Manages the Melvin's travel across the map and the scanning of it,
    avoid the scan of the row if already done it (descent immediately)

    """
    if init.scanx == 0:
        data = init.json.loads(init.requests.get(init.url + "observation").content)
        init.y_center = data['telemetry']['y']
        init.x_scan = utility.see_if_takephoto(init.y_center) #Compute the common x intervals between all y, from the current y

    exit = utility.watch_cover_zone(init.y_center) #If row already covered, starting descent
    init.scanx += 1

    if init.scanx <= 40 and exit is not True:
        if init.block is not True:
            init.requests.put(init.url + "control", json={"state": 'active', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
            init.time.sleep(1)

        response_img = init.requests.get(init.url + "image").content
        data = init.json.loads(init.requests.get(init.url + "observation").content)
        center = data['telemetry']['x']

        if init.scanx == 1: #Compute the x where to start taking photo in the current row
            init.x_start = center - OFFSET if center - OFFSET > 0 else RIGHT_BORDER + (center - OFFSET)

        out_of = True
        for elem in init.x_scan: #Checking when outside the already covered zone
            left = center - OFFSET if center - OFFSET > 0 else 0
            right = center + OFFSET if center + OFFSET < RIGHT_BORDER else RIGHT_BORDER
            if elem[0] <= left <= elem[1] and elem[0] <= right <= elem[1] and elem[0] <= center <= elem[1]:
                out_of = False

        if out_of: #If outside of at least one zone, taking the photo
            utility.take_photo(response_img, data['telemetry']['angle'], center, data['telemetry']['y'], map=True,center=center)

        if init.block is not True:
            init.requests.put(init.url + "control", json={"state": 'charge', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
        return

    if init.scanx == 41 or exit is True:
        print("Starting mapping's descent",init.datetime.now())
        init.sched.pause_job('mapping') #Pausing mapping job

        if init.scanx == 41: #If row completed, updating the interval to [0, 21600]
            utility.cover_zone(init.y_center, 0, RIGHT_BORDER)

        time_to_descent = utility.time_to_closest_y(init.y_center)
        init.scanx = 0

        if init.block is not True:
            init.requests.put(init.url + "control", json={"state": 'active', "camera_angle": 'wide', "vel_x": 10, "vel_y": 1})
            init.time.sleep(3)
            init.requests.put(init.url + "control", json={"state": 'charge', "camera_angle": 'wide', "vel_x": 10, "vel_y": 1})

        if init.block is not True:
            init.time.sleep(time_to_descent)
            init.requests.put(init.url + "control", json={"state": 'active', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
            init.time.sleep(3)
            init.requests.put(init.url + "control", json={"state": 'charge', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
            init.sched.resume_job('mapping')

        print("Descent ended, restarting mapping",init.datetime.now())
        return

    return
