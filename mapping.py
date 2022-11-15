import init
import melvin
import utility

# Function that scan the map and saves images
OFFSET = 300
RIGHT_BORDER = 21600


def scan_map():
    if init.scanx == 0:
        response_obs = init.requests.get(init.url + "observation").content
        data = init.json.loads(response_obs)
        init.y_center = data['telemetry']['y']
        init.x_scan = utility.see_if_takephoto(init.y_center)  # we also compute new only the first time
        print(init.x_scan)
    exit = utility.watch_cover_zone(init.y_center)

    init.scanx += 1

    if init.scanx <= 40 and exit is not True:
        if init.block is not True:
            init.requests.put(init.url + "control",
                              json={"state": 'active', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
        init.time.sleep(1)
        if init.block is not True:
            response_img = init.requests.get(init.url + "image").content
            response_obs = init.requests.get(init.url + "observation").content
            data = init.json.loads(response_obs)
            center = data['telemetry']['x']
            if init.scanx == 1:
                # variabile globale che mi fa da start per la sessione corrente
                init.x_start = center - OFFSET if center - OFFSET > 0 else RIGHT_BORDER + (
                        center - OFFSET)  # x_start = x attuale - offset (fittato)

            out_of = True
            for elem in init.x_scan:

                left = center - OFFSET if center - OFFSET > 0 else 0

                right = center + OFFSET if center + OFFSET < RIGHT_BORDER else RIGHT_BORDER

                if elem[0] <= left <= elem[1] and elem[0] <= right <= elem[1] and elem[0] <= center <= elem[1]:
                    out_of = False

            if out_of:
                print("map fatto foto", center)
                utility.cover_zone(init.y_center, init.x_start, (
                            center + OFFSET) % RIGHT_BORDER)  # ogni foto scattata aggiorniamo l'intervallo a [x_start, x attuale + offset (fittato)]
                utility.take_photo(response_img, data['telemetry']['angle'], center, data['telemetry']['y'], map=True)

            print("sono passato", center)
        if init.block is not True:
            init.requests.put(init.url + "control",
                              json={"state": 'charge', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
        print("dado")
        return

    if init.scanx == 41 or exit is True:
        init.sched.pause_job('mapping')
        if init.scanx == 41:
            utility.cover_zone(init.y_center, 0,
                               RIGHT_BORDER)  # sappiamo di avere completato la riga intera, mettiamo l'intervallo a [0, 21600]
        t = utility.time_to_closest_y(init.y_center)
        init.scanx = 0
        init.sched.pause_job('mapping')
        if init.block is not True:
            init.requests.put(init.url + "control",
                                  json={"state": 'active', "camera_angle": 'wide', "vel_x": 10, "vel_y": 1})
            init.time.sleep(3)
            if init.block is not True:
                init.requests.put(init.url + "control",
                                  json={"state": 'charge', "camera_angle": 'wide', "vel_x": 10, "vel_y": 1})
        if init.block is not True:
            init.time.sleep(t)
        if init.block is not True:
            init.requests.put(init.url + "control",
                                  json={"state": 'active', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
            init.time.sleep(3)
            if init.block is not True:
                init.requests.put(init.url + "control",
                                  json={"state": 'charge', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
            init.sched.resume_job('mapping')
        return

    return
