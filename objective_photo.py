import json
import time

import requests
import melvin
import movement
import utility
import init

def photo(n_foto, id):
    print("INIT: ",init.taken)
    init.taken += 1
    if n_foto >= init.taken:
        response = requests.get(init.url + "objectives").content
        data = json.loads(response)
        data = data['objectives']
        response_img = requests.get(init.url + "image").content
        utility.take_photo(response_img, str(id)+'-'+str(init.taken))
        for obj in data:
            if obj['id'] == str(id) and obj['done'] is True:
                init.sched.remove_job('photo')
                init.taken = 0
                init.active_objectives.pop(0)
                melvin.reset()
    else:
        init.sched.remove_job('photo')
        init.taken = 0
        init.active_objectives.pop(0)
        melvin.reset()
    return

def photographer(lens, id):
    lenses = {'narrow': 51, 'normal': 68, 'wide': 85}  # 85% della size delle lenti
    response =requests.put(init.url + "control",
                 json={"state": 'active', "camera_angle": lens, "vel_x": 10, "vel_y": 0})  # SETTIAMO LA LENTE
    init.sched.remove_job('p')
    print(response)
    init.time.sleep(2)
    response_img = requests.get(init.url + "image").content
    print(response_img)
    utility.take_photo(response_img, "first")

    if init.t_photo % lenses[lens] == 0:
        n_foto = int(init.t_photo / lenses[lens])
    else:
        n_foto = int(init.t_photo // lenses[lens]) + 1
    print('n_photo',n_foto)
    init.sched.add_job(lambda: photo(n_foto - 1, id), 'interval', seconds=lenses[lens], id='photo', max_instances=10)
    return


def photo_row(n_foto, idx_row, max_row):
    init.taken += 1
    if n_foto >= init.taken:
        print("SCATTO ROW")
        response_img = requests.get(init.url + "image").content
        utility.take_photo(response_img, init.taken, row=idx_row)
    else:
        init.sched.remove_job('photo_row' + str(idx_row))
        init.taken = 0
        if idx_row == max_row:
            init.active_objectives.pop(0)
            melvin.reset()
    return


def start_photo_row(n_foto, idx_row, interval, max_row):
    init.sched.remove_job('start_photo_row' + str(idx_row))
    response_img = requests.get(init.url + "image").content
    utility.take_photo(response_img, 'first', row=idx_row)
    init.sched.add_job(lambda: photo_row(n_foto-1, idx_row, max_row), 'interval', seconds=interval,
                       id='photo_row' + str(idx_row),
                       max_instances=10)
    return


def photographer_multiple(lens, n_photo, coordinates):
    dic = {'narrow': 55, 'normal': 75, 'wide': 95}
    t_y = {'narrow': 90, 'normal': 110, 'wide': 140}
    init.sched.remove_job('pm')
    requests.put(init.url + "control", json={"state": 'active', "camera_angle": lens, "vel_x": 10, "vel_y": 0})
    tmp_time = 1
    descent_time = t_y[lens]  # calculate y time calculate_y() tempo per scendere in base alla lente usata
    for idx in range(1, len(coordinates)):
        init.sched.add_job(lambda: start_photo_row(n_photo, idx, dic[lens], len(coordinates)), 'interval',
                           seconds=tmp_time,
                           id='start_photo_row' + str(idx),
                           max_instances=1)
        init.sched.add_job(lambda: movement.descent(descent_time, idx), 'interval',
                           seconds=tmp_time + (dic[lens] * (n_photo - 1))+2,
                           id='descent' + str(idx),
                           max_instances=1)
        tmp_time += ((dic[lens] * (n_photo - 1)) + descent_time + 2)

    init.sched.add_job(lambda: start_photo_row(n_photo, len(coordinates), dic[lens], len(coordinates)), 'interval',
                       seconds=tmp_time,
                       id='start_photo_row' + str(len(coordinates)),  # forse cast int
                       max_instances=1)
    return



def area(zone, lens, coverage):
    lenses = {'narrow': 550, 'normal': 750, 'wide': 950}
    t_y = {'narrow': 90, 'normal': 110, 'wide': 140}  # Tempi di discesa a velocità 8
    off = {'narrow': 586, 'normal': 786, 'wide': 986}
    # if else for border limit cases
    if zone['left'] > zone['right']:
        distance = (int((21600 - zone['left'] + zone['right']) * coverage) // 2) + 1
        center = (zone['left'] + distance // 2) % 21600
    else:
        distance = (int((zone['right'] - zone['left']) * coverage) // 2) + 1
        center = (zone['left'] + zone['right']) // 2

    # compute the new borders / x
    new_left = int((center - distance) % 21600)  # Start delle foto
    new_right = int((center + distance) % 21600)
    if (distance * 2) % lenses[lens] == 0:
        n_photo = (distance * 2)/lenses[lens]
    else:
        n_photo = ((distance * 2) // lenses[lens]) + 1
    coordinates = []
    if zone['top'] > zone['bottom']:  # Accavvallamento y con bordo
        distance_y = (int((10800 - zone['top'] + zone['bottom']) * coverage) // 2) + 1
        center_y = (zone['top'] + distance_y // 2) % 10800
    else:
        distance_y = (int((zone['bottom'] - zone['top']) * coverage) // 2) + 1
        center_y = (zone['bottom'] + zone['top']) // 2
    new_top = int((center_y - distance_y) % 10800)
    new_bottom = int((center_y + distance_y) % 10800)

    y_start = new_top + int(off[lens] / 2)
    offset = off[lens]  # Basato sulla lente wide
    if new_bottom < new_top:  # Caso in cui la y va oltre limite
        pixel_size = 10800 - new_bottom + new_top
        lim_inf = 10800 + new_bottom
    else:
        pixel_size = new_bottom - new_top  # 1634
        lim_inf = new_bottom
    pixel_size -= offset // 2  # Offset /2 = 293

    coordinates.append(y_start)
    # Calculate y coordinates
    while lim_inf - y_start > ((lenses[lens] + 50) / 2):  # Aggiungo x per movimento diagonale
        if pixel_size >= offset:
            pixel_size -= offset
        else:
            offset = pixel_size // 2
        y_start = (y_start + offset) % 10800
        if y_start < new_top:
            lim_inf = new_bottom
        coordinates.append(y_start)
    expected_t = ((distance // 5) + 1) * len(coordinates) + ((len(coordinates) - 1) * t_y[lens])
    return [new_left, new_right, n_photo, coordinates, expected_t]
