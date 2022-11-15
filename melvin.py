
# !/usr/bin/env python3
import time
import calculations
import init
import objective_photo
import utility
import mapping


def start_up():
    print("starto")
    init.requests.put(init.url + "control",json={"state": "active", "camera_angle": "wide", "vel_x": 10, "vel_y": 0})
    init.real_vx = 10
    init.real_vy = 0
    print("PRE: ", init.datetime.now())
    time.sleep(22)
    print("POST: ", init.datetime.now())
    init.requests.put(init.url + "control",json={"state": "charge", "camera_angle": "wide", "vel_x": 10, "vel_y": 0})
    resume()
    init.sched.start()


# resume mapping and objectives JOB
def resume():
    print("resume")
    init.block = False
    init.sched.add_job(objectives, 'interval', seconds=60, id='objectives', max_instances=1)
    init.sched.add_job(mapping.scan_map, 'interval', seconds=57, id='mapping', max_instances=1)


# called from a job each minute for search active objectives
# select only the active ones
def objectives():
    print("Sto osservando gli obbiettivi")
    response = init.requests.get(init.url + "objectives").content
    d = init.json.loads(response)
    d = d['objectives']
    lines = []
    for x in d:
        lines.append(x)
    for x in init.data:
        lines.append(x)
    init.active_objectives = []
    now = init.datetime.now()
    """
    lines.sort(key=lambda k: (k['done'] == True, k['start'] ), reverse=False)
    if len(lines) != 0:
        next_date_obj = lines[0]['start']
        if (next_date_obj - now).total_seconds() > 8100:
            pause()
            start_date = init.datetime.now()
            end_date = init.timedelta(hours=1, minutes=28, seconds=0)
            init.sched.add_job(mappingwide.mappingwide, 'interval', seconds=14, start_date=start_date, end_date=end_date)
            init.sched.add_job(melvin.reset,'date',run_date = end_date )
	    return
   """
    # filtriamo obbiettivi e prendiamo solo quelli attivi e che non abbiamo completato e sono attivi se unknown modifico già
    for x in lines:
        s, e = utility.convert_to_datetime(x['start'], x['end'])
        print("S;E :", s, e)
        if s < now < e:
            if str(x['done']) == 'false':
                if 'unknown' not in x['zone']:
                    init.saved_obj[x['name']] = x['zone']
                    init.active_objectives.append(x)
                else:
                    if x['name'] in init.saved_obj:  # C'è riferimento #todo vedere se si puo x['zone] =
                        x['zone'] = init.saved_obj[x['name']]
                        init.active_objectives.append(x)
                    #else:
                        #lancio qualcosa che me lo trova e quando lo trova salva le coordinate della foto e da li trova una certa area
                        #id ->done -> salvo
                        #metodo

    if len(init.active_objectives) > 0:
        print("Ho trovato obbiettivi attivi")
        calculations.calculator()
    return


def go_and_scan(x, y, lens, id, response, coordinates=[], n_photo=0, is_multiple=False):
    if init.block is not True:
        pause()

    init.requests.put(init.url + "control",
                      json={"state": "active", "camera_angle": "wide", "vel_x": x[0], "vel_y": y[0]})
    init.real_vy = y[0]
    init.real_vx = x[0]

    # manage the start cruise and deceleration job
    utility.cruise_dec(x, y)
    utility.create_change_dir(id,response)

    # start photo job
    if is_multiple:
        print(x,"---x---",y,"-----y----")
        print("tempo prima di scan multiple",x[1])
        print("scan multiple")
        objective_photo.photographer_multiple(lens, n_photo, coordinates, x[1])
    else:
        print(x,"---x---",y,"-----y----")
        print("tempo prima di scan multiple",x[1])
        print("scan single")
        init.sched.add_job(lambda: objective_photo.photographer(lens, id), 'interval', seconds=x[1], id='p',
                           max_instances=1)


# Pause mapping and objectives when we start the route to one objective
def pause():
    print("pause")
    init.scanx = 0
    init.block = True
    init.sched.remove_job('objectives')
    init.sched.remove_job('mapping')


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
            return
        else:
            print("RESUME THE TOUR")
            # rimetto l'ordine del sort precedente se non ce ne sono di nuovi
            init.active_objectives = tmp
            resume_the_tour()
            return
    else:
        if init.real_vx != 10:
            init.requests.put(init.url + "control",
                              json={"state": 'active', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
            init.time.sleep(42)
            init.requests.put(init.url + "control",
                              json={"state": 'charge', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
        resume()
        return


def resume_the_tour():
    print("resumethetour")
    response = init.requests.get(init.url + "observation").content
    data = init.json.loads(response)

    curr_x = int(data['telemetry']['vx'])
    curr_y = int(data['telemetry']['vy'])
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
    pixel_photo = ((zone['bottom'] - zone['top']) % 10800 ) * coverage

    dic_limit = {'narrow': 550, 'normal': 750, 'wide': 950}

    if pixel_photo > dic_limit[lens]:  # multiple layer photos
        photo_data = objective_photo.area(zone, lens, coverage)
        n_photo = photo_data[2]
        coordinates = photo_data[3]
        expected_t = photo_data[4]
        t_to_target -= expected_t  # we remove time of photo from the total avaiable time we have
        res = calculations.calculate_distance_time_fuel(photo_data[0], coordinates[0], t_to_target, curr_x, curr_y,
                                                        coord_x, coord_y, True)
        if len(res) != 0:
            print("lancio un obbiettivo multi layer da resumethetour")
            for el in init.data:
                if el['id'] == init.active_objectives[0]['id']:
                    print("Ho modificato obbiettivo a done -> true")
                    el['done'] = True
            print(res[init.vel_route[0]][0])
            print("RES_resume_multi: ",res)
            go_and_scan(res[init.vel_route[0]][0], res[init.vel_route[0]][1], lens, id, init.active_objectives[0] ,coordinates, n_photo, True)
            return
    else:  # ONE layer
        dist_ = calculations.dist(final_x, x_end_target)
        init.t_photo = dist_ / 10
        t_to_target -= init.t_photo
        res = calculations.calculate_distance_time_fuel(final_x, final_y, t_to_target, curr_x, curr_y,
                                                        coord_x, coord_y, True)
        if len(res) != 0:
            for el in init.data:
                if el['id'] == init.active_objectives[0]['id']:
                    print("Ho modificato obbiettivo a done -> true")
                    el['done'] = True
            print("lancio un obbiettivo single layer da resumethetour")
            print("RES_resume_single: ",res)
            go_and_scan(x = res[init.vel_route[0]][0],y = res[init.vel_route[0]][1],lens = lens,id = id,response = init.active_objectives[0])
            #[[[vel,t,car,tacc,tdec,tcruise],[vel,t,car,tacc,tdec,tcruise]],[[vel,t,car,tacc,tdec,tcruise],[vel,t,car,tacc,tdec,tcruise]]]
            return
    if init.block is False:
        resume()
    #assicurarsi che riparta mapping e objective
    print("errore resumethetour res vuoto")
    return


if __name__ == '__main__':
    start_up()
