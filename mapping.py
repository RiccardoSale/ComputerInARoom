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
        init.x_scan = utility.see_if_takephoto(init.y_center) #we also compute new only the first time
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

            if init.scanx == 1:
                # variabile globale che mi fa da start per la sessione corrente
                init.x_start = data['telemetry']['x'] - OFFSET if data['telemetry']['x'] - OFFSET > 0 else RIGHT_BORDER + (data['telemetry']['x'] - OFFSET) #x_start = x attuale - offset (fittato)


            out_of = True
            for elem in init.x_scan:
                if (elem[0] <=data['telemetry']['x']<= elem[1]): #elem contiene la zona gia scannata
                    out_of = False

            if out_of:
                print("map fatto foto", data['telemetry']['x'])
                utility.cover_zone(init.y_center, init.x_start, (data['telemetry'][
                                                                     'x'] + OFFSET) % RIGHT_BORDER)  # ogni foto scattata aggiorniamo l'intervallo a [x_start, x attuale + offset (fittato)]
                utility.take_photo(response_img, data['telemetry']['angle'], data['telemetry']['x'],
                                   data['telemetry']['y'],
                                   map=True)
        print("sono passato")
        if init.block is not True:
            init.requests.put(init.url + "control",
                              json={"state": 'charge', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
        return

    if init.scanx == 41 or exit is True:

        if init.scanx == 41:
            utility.cover_zone(init.y_center, 0, RIGHT_BORDER) #sappiamo di avere completato la riga intera, mettiamo l'intervallo a [0, 21600]

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
