# !/usr/bin/env python3
import time
import calculations
import init
import objective_photo
import utility
import mapping


def convert_to_datetime(s, e):
    s = s.split('+')[0]
    s = init.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')
    e = e.split('+')[0]
    e = init.datetime.strptime(e, '%Y-%m-%dT%H:%M:%S')
    return [s, e]


# resume mapping and objectives JOB
def resume():
    init.block = False
    init.cd = init.cur_dir + '/map'
    init.sched.add_job(objectives, 'interval', seconds=60, id='objectives', max_instances=1)
    init.sched.add_job(mapping.scan_map, 'interval', seconds=57, id='mapping', max_instances=1)


def pause():
    init.scanx = 0
    init.block = True
    init.sched.remove_job('objectives')
    init.sched.resume_job('mapping')


def start_up():
    print("starto")
    init.requests.put(init.url + "control",
                      json={"state": "active", "camera_angle": "wide", "vel_x": 10, "vel_y": 0})
    init.real_vx = 10
    init.real_vy = 0
    print("PRE: ", init.datetime.now())
    time.sleep(22)
    print("POST: ", init.datetime.now())
    init.requests.put(init.url + "control",
                      json={"state": "charge", "camera_angle": "wide", "vel_x": 10, "vel_y": 0})
    resume()
    init.sched.start()


def reset():
    print("Sono in reset")
    # Controllo se ci sono obbiettivi da fare attivi in
    if len(init.active_objectives) > 0:  # ho ancora obbiettivi da fare dato il the tour che avevo "lanciato"
        if init.real_vx != 10:
            init.requests.put(init.url + "control",
                              json={"state": 'active', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
            init.time.sleep(42)
            init.requests.put(init.url + "control",
                              json={"state": 'charge', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
            # DOVREI CAPIRE SE GLI OBBIETTTIVI SONO CAMBIATI -> SE SONO CAMBIATI LANCIO CALCULATION ??
            # lancio objectives una volta se il numero è diverso allora sono cambiati ??#TODO CONTROLLARE
        tmp = init.active_objectives
        objectives()
        if len(tmp) != len(init.active_objectives):
            calculations.calculator()
        else:
            print("RESUME THE TOUR")
            # rimetto l'ordine del sort precedente se non ce ne sono di nuovi
            init.active_objectives = tmp
            resume_the_tour()
    else:
        if init.real_vx != 10:
            init.requests.put(init.url + "control",
                              json={"state": 'active', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
            init.time.sleep(42)
            init.requests.put(init.url + "control",
                              json={"state": 'charge', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
        resume()

# called from a job each minute for search active objectives
# select only the active ones
def objectives():
    print("Sto osservando gli obbiettivi")
    # response = requests.get(url + "objectives").content
    # data = json.loads(response)
    # data = data['objectives']

    lines = []
    for x in init.data:
        lines.append(x)
    now = init.datetime.now()
    print("NOW", now)
    init.active_objectives = []
    # filtriamo obbiettivi e prendiamo solo quelli attivi e che non abbiamo completato e sono attivi se unknown modifico già
    for x in lines:
        s, e = convert_to_datetime(x['start'], x['end'])
        print("S;E :", s, e)
        if s < now < e:
            if not x['done']:
                if 'unknown' not in x['zone']:
                    init.saved_obj[x['name']] = x['zone']
                    init.active_objectives.append(x)
                else:
                    if x['name'] in init.saved_obj:  # C'è riferimento #todo vedere se si puo x['zone] =
                        x['zone'] = init.saved_obj[x['name']]
                        init.active_objectives.append(x)

    # se troviamo obbiettivi attivi chiamiamo calculator
    if len(init.active_objectives) > 0:
        calculations.calculator()
    return


def resume_the_tour():
    print("resumethetour")
    response = init.requests.get(init.url + "observation").content
    data = init.json.loads(response)

    curr_x = int(data['telemetry']['vx'])  # vx attuale
    curr_y = int(data['telemetry']['vy'])  # vy attuale
    # salvo y attuale #Nelle iterazioni succ sarà la coordinata del punto appena fatto
    coord_y = int(data['telemetry']['y'])
    coord_x = int(data['telemetry']['x'])

    zone = init.active_objectives[0]['zone']
    final_x = zone['left']
    final_y = (zone['top'] + zone['bottom']) // 2
    x_end_target = zone['right']

    t_to_target = utility.delta_time(init.active_objectives[0]['end'])
    t_to_target = int(int(t_to_target.total_seconds()) * 0.9)  # Secondi a finte obiettivo con offset 10%

    lens = init.active_objectives[0]['optic_required'].lower()
    id = init.active_objectives[0]['id']

    coverage = int(init.active_objectives[0]['coverage_required']) / 100
    pixel_photo = (zone['top'] - zone['bottom']) * coverage

    dic_limit = {'narrow': 550, 'normal': 750, 'wide': 950}

    if pixel_photo > dic_limit[lens]:  # multiple layer photos
        photo_data = objective_photo.area(zone, lens, coverage)
        n_photo = photo_data[2]
        coordinates = photo_data[3]
        expected_t = photo_data[4]
        t_to_target -= expected_t  # we remove time of photo from the total avaiable time we have
        res = calculations.calculate_distance_time_fuel(photo_data[0], coordinates[0], t_to_target, curr_x, curr_y,
                                                        coord_x, coord_y, True)
        go_and_scan_multiple(res[init.vel_route][0], res[init.vel_route][1], coordinates, lens, n_photo, id)
    else:  # ONE layer
        dist_ = calculations.dist(final_x, x_end_target)
        init.t_photo = dist_ / 10
        t_to_target -= init.t_photo
        res = calculations.calculate_distance_time_fuel(final_x, final_y, t_to_target, curr_x, curr_y,
                                                        coord_x, coord_y, True)
        go_and_scan_single(res[init.vel_route][0], res[init.vel_route][1], lens, id)


def go_and_scan_multiple(x, y, coordinates, lens, n_photo, id):
    pause()
    print("sono dentro scan multiple")
    # create objective folder with id
    utility.create_change_dir(id)
    # we now start the cruise for the left border of the photo
    init.requests.put(init.url + "control",
                      json={"state": "active", "camera_angle": "wide", "vel_x": x[0], "vel_y": y[0]})
    print("VERE", x[0], y[0])
    init.real_vy = y[0]
    init.real_vx = x[0]
    # manage the start cruise and deceleration job
    utility.cruise_dec(x, y)
    # start job for multiple layer photo
    init.sched.add_job(lambda: objective_photo.photographer_multiple(lens, n_photo, coordinates), 'interval',
                       seconds=x[1] - 1, id='pm',
                       max_instances=1)


def go_and_scan_single(x, y, lens, id):
    pause()
    print('lens',lens)
    print('t_photo',init.t_photo)
    utility.create_change_dir(id)
    init.requests.put(init.url + "control",
                      json={"state": "active", "camera_angle": "wide", "vel_x": x[0], "vel_y": y[0]})
    # manage the start cruise and deceleration job
    init.real_vy = y[0]
    init.real_vx = x[0]
    utility.cruise_dec(x, y)
    init.sched.add_job(lambda: objective_photo.photographer(lens, id), 'interval', seconds=x[1], id='p',
                       max_instances=1)


if __name__ == '__main__':
    start_up()
