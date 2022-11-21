# !/usr/bin/env python3
import init
import calculations
import objective_photo
import utility
import mapping


def start_up():
    """
    Starting up the MELVIN and setting (10,0) velocity, resuming mapping and objective jobs and starting the scheduler

    """

    print("Starting up")
    init.requests.put(init.url + "control",json={"state": "active", "camera_angle": "wide", "vel_x": 10, "vel_y": 0})
    init.real_vx = 10
    init.real_vy = 0
    init.time.sleep(22) #Acceleration time from 0 to 10
    init.requests.put(init.url + "control",json={"state": "charge", "camera_angle": "wide", "vel_x": 10, "vel_y": 0})
    resume()
    init.sched.start()


def resume():
    """
    Resuming objectives and mapping jobs, release thread lock

    """

    init.block = False
    init.sched.add_job(objectives, 'interval', seconds=60, id='objectives', max_instances=1)
    init.sched.add_job(mapping.scan_map, 'interval', seconds=57, id='mapping', max_instances=1)


def pause():
    """
    Stops objectives and mapping while dealing with an objective

    """

    print("Pause")
    init.scanx = 0
    init.block = True
    init.sched.remove_job('objectives')
    init.sched.remove_job('mapping')


def objectives():
    """
    Function that when active check every 60 seconds how many and what are the active objectives and then
    provides them to calculator that verifies and decides whether to start acquiring them.

    """

    print("Observing objectives")
    known_objectives = init.json.loads(init.requests.get(init.url + "objectives").content)['objectives']
    all_objectives = []

    #Adding all available objectives
    for x in known_objectives:
        all_objectives.append(x)
    for x in init.data: #Adding custom objectives
        all_objectives.append(x)
    init.active_objectives = []
    now = init.datetime.now()

    for x in all_objectives:
        s, e = utility.convert_to_datetime(x['start'], x['end'])
        if x['id'] not in init.past_objective:
            if s < now < e:
                if str(x['done']) == 'False':
                    if 'unknown' not in x['zone']:
                        init.active_objectives.append(x)

    if len(init.active_objectives) > 0:
        print("Active objectives found")
        calculations.calculator()
    return


def go_and_scan(x, y, lens, id, response, coordinates=[], n_photo=0, is_multiple=False):
    """
    Manages the acquisition and the travel to the objective

    :param x: x velocity
    :param y: y velocity
    :param lens: objective's lens
    :param id: objective's id
    :param response: objective's data
    :param coordinates: list of y to reach with photographer_multiple
    :param n_photo: number of photo
    :param is_multiple: True if a multi-layer objective
    """
    
    if init.block is not True:
        pause()

    init.requests.put(init.url + "control", json={"state": "active", "camera_angle": "wide", "vel_x": x[0], "vel_y": y[0]})
    init.real_vy = y[0]
    init.real_vx = x[0]

    #Manage the start cruise and deceleration job
    utility.cruise_dec(x, y)
    utility.create_change_dir(id,response)
    init.past_objective.add(id)

    #Start photo job
    if is_multiple:
        objective_photo.photographer_multiple(lens, n_photo, coordinates, x[1], id)
    else:
        objective_photo.photographer(lens, id, x[1], response['zone'])
    return


def count_active_objectives():
    """
    Finds the currently active objectives
    """
    response = init.requests.get(init.url + "objectives").content
    d = init.json.loads(response)
    d = d['objectives']
    lines = []
    for x in d:
        lines.append(x)
    for x in init.data:
        lines.append(x)
    active = []
    now = init.datetime.now()
    for x in lines:
        s, e = utility.convert_to_datetime(x['start'], x['end'])
        print("S;E :", s, e)
        if s < now < e:
            if str(x['done']) == 'False':
                if 'unknown' not in x['zone']:
                    active.append(x)
    return len(active)

def reset():    
    """
    Manages the restart of the mapping or travel to new objectives after the complete acquisition of an objective

    """

    print("Reset")

    if init.real_vx != 10: #Restoring (10,0) velocity
        init.requests.put(init.url + "control", json={"state": 'active', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})
        init.time.sleep(42)
        init.requests.put(init.url + "control", json={"state": 'charge', "camera_angle": 'narrow', "vel_x": 10, "vel_y": 0})

    #Checking if there are still active objectives
    if len(init.active_objectives) > 0:
        num = count_active_objectives()
        #If new objective are found recalculating route with calculator, otherwise calling resume the tour
        if len(init.active_objectives) != num:
            calculations.calculator()
            return
        else:
            resume_the_tour()
            return
    else:
        resume()
        return


def resume_the_tour():
    """
    Starts the travel to the first active objective reachable

    """

    data = init.json.loads(init.requests.get(init.url + "observation").content)
    curr_x = int(data['telemetry']['vx'])
    curr_y = int(data['telemetry']['vy'])
    coord_y = int(data['telemetry']['y'])
    coord_x = int(data['telemetry']['x'])
    zone = init.active_objectives[0]['zone']
    final_x = zone['left']
    final_y = (zone['top'] + zone['bottom']) // 2
    x_end_target = zone['right']

    t_to_target = utility.delta_time(init.active_objectives[0]['end'])
    t_to_target = int(int(t_to_target.total_seconds()) * 0.9) #Removing 10% of the available time to arrive at the objective in advance
    lens = init.active_objectives[0]['optic_required'].lower()
    id = init.active_objectives[0]['id']

    coverage = int(init.active_objectives[0]['coverage_required']) / 100
    pixel_photo = ((zone['bottom'] - zone['top']) % 10800 ) * coverage #Pixels required to cover all the y area including the coverage required
    dic_limit = {'narrow': 550, 'normal': 750, 'wide': 950}

    if pixel_photo > dic_limit[lens]: #Multi-layer photos
        photo_data = objective_photo.area(zone, lens, coverage)
        n_photo = photo_data[2]
        coordinates = photo_data[3]
        expected_t = photo_data[4]
        t_to_target -= expected_t  #Removing the time of photo from the total avaiable time
        res = calculations.calculate_distance_time_fuel(photo_data[0], coordinates[0], t_to_target, curr_x, curr_y, coord_x, coord_y, True)
        if len(res) != 0:
            print("Starting objective from resume the tour, multi-layer")
            print(res[init.vel_route[0]][0])
            go_and_scan(res[init.vel_route[0]][0], res[init.vel_route[0]][1], lens, id, init.active_objectives[0], coordinates, n_photo, True)
            return
    else: #Single layer objective
        dist_ = calculations.dist(final_x, x_end_target)
        init.t_photo = dist_ / 10
        t_to_target -= init.t_photo
        res = calculations.calculate_distance_time_fuel(final_x, final_y, t_to_target, curr_x, curr_y, coord_x, coord_y, True)
        if len(res) != 0:
            print("Starting objective from resume the tour, single layer")
            go_and_scan(x = res[init.vel_route[0]][0],y = res[init.vel_route[0]][1],lens = lens,id = id,response = init.active_objectives[0])
            return
    if init.block is True:
        resume()

    return


if __name__ == '__main__':
    start_up()
