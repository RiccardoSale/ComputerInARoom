import melvin
import movement
import utility
import init
import stitching
import calculations


def photo(n_photo, id):
    """
    Takes all the necessary photos in single layer objectives
    
    :param n_photo: number of photo
    :param id: objective's id
    """

    init.taken += 1

    #Taking photo if n_photo more then taken
    if n_photo >= init.taken:
        data = init.json.loads(init.requests.get(init.url + "objectives").content)['objectives']
        response_img = init.requests.get(init.url + "image").content
        utility.take_photo(response_img, str(id) + '-' + str(init.taken))

        for obj in data:
            if obj['id'] == str(id) and obj['done'] is True: #Checkin if objective is done
                #Stitching and compressing the image
                stitching.stitch(init.cd)
                utility.compress_file(init.cd+"/objective_"+str(id)+".png")
                init.sched.remove_job('photo')
                init.taken = 0
                init.active_objectives.pop(0)
                melvin.reset()
    else:
        # Stitching and compressing the image
        stitching.stitch(init.cd)
        utility.compress_file(init.cd+"/objective_"+str(id)+".png")
        init.sched.remove_job('photo')
        init.taken = 0
        init.active_objectives.pop(0)
        melvin.reset()
    return


def photographer(lens, id, wait, response):
    """
    Manages the acquisition of single-layer objectives
    
    :param lens: objective's lens
    :param id: objective's id
    :param wait: time to reach the objective
    :param response: objective's zone data
    """

    init.time.sleep(wait - 1) #Waiting objective's travel time
    lenses = {'narrow': 51, 'normal': 68, 'wide': 85}
    init.requests.put(init.url + "control", json={"state": 'active', "camera_angle": lens, "vel_x": 10, "vel_y": 0})

    #Calculation of n_photo based on the time t_photo and the time that each lens need between two photos
    if init.t_photo % lenses[lens] == 0:
        n_photo = int(init.t_photo / lenses[lens])
    else:
        n_photo = int(init.t_photo // lenses[lens]) + 1

    #If the objective's area fit in a single foto, shifting MELVIN to the center of the area
    if n_photo == 1:
        dist = calculations.dist(response['left'], response['right'], 21600) // 2
        if dist % 10 == 0:
            time = dist / 10
        else:
            time = (dist // 10) + 1
        init.time.sleep(time)

    init.time.sleep(1)
    response_img = init.requests.get(init.url + "image").content
    utility.take_photo(response_img, "first")
    #Starting job for the remaining photos, setting the interval between photos with lenses[lens]
    init.sched.add_job(lambda: photo(n_photo - 1, id), 'interval', seconds=lenses[lens], id='photo', max_instances=10)
    return


def photo_row(n_photo, idx_row, max_row, lens, id):
    """
    Takes all the photos in a row for multi-layer objectives
    
    :param n_photo: number of photo for each row 
    :param idx_row: current row
    :param max_row: last row to scan
    :param lens: objective's lens
    :param id: objective's id
    """

    init.taken += 1
    if n_photo >= init.taken:
        init.requests.put(init.url + "control", json={"state": 'active', "camera_angle": lens, "vel_x": init.real_vx, "vel_y": init.real_vy})
        init.time.sleep(1)
        response_img = init.requests.get(init.url + "image").content
        utility.take_photo(response_img, init.taken, row=idx_row)
    else:
        init.taken = 0
        init.sched.remove_job('photo_row' + str(idx_row))
        if idx_row == max_row:
            print("Objective's photos acquired, stitching and compressing images")
            stitching.stitch(init.cd)
            utility.compress_file(init.cd+"/objective_"+str(id)+".png")
            init.active_objectives.pop(0)
            melvin.reset()
    return


def start_photo_row(n_photo, idx_row, interval, max_row, lens, id):
    """
    Takes objective first photo and schedules the row acquisition
    
    :param n_photo: number of photo for each row 
    :param idx_row: current row
    :param interval: seconds between each row
    :param max_row: last row to scan
    :param lens: objective's lens
    :param id: objective's id
    """

    init.requests.put(init.url + "control", json={"state": 'active', "camera_angle": lens, "vel_x": init.real_vx, "vel_y": init.real_vy})
    init.time.sleep(1)
    response_img = init.requests.get(init.url + "image").content
    utility.take_photo(response_img, 'first', row=idx_row)
    init.sched.add_job(photo_row, args=[n_photo - 1, idx_row, max_row, lens, id], trigger='interval', seconds=interval,
                       id='photo_row' + str(idx_row),
                       max_instances=10)
    return


def photographer_multiple(lens, n_photo, coordinates, wait, id):
    """
    Manages multi-layer objectives acquisition
    
    :param lens: objective's lens
    :param n_photo: number of photo for each row 
    :param coordinates: y coordinates of all the layers
    :param wait: time to reach the objective
    :param id: objective's id
    """

    init.time.sleep(wait) #Waiting travel time
    lenses = {'narrow': 55, 'normal': 75, 'wide': 95}
    t_y = {'narrow': 90, 'normal': 110, 'wide': 140}
    init.requests.put(init.url + "control", json={"state": 'charge', "camera_angle": lens, "vel_x": 10, "vel_y": 0})
    tmp_time = 1
    count = 1
    descent_time = t_y[lens]

    #Starts all the jobs for each objective's row
    while count < len(coordinates):
        init.time.sleep(tmp_time)
        start_photo_row(n_photo, count, lenses[lens], len(coordinates), lens, id)
        init.time.sleep((tmp_time + (lenses[lens] * (n_photo - 1))))
        movement.descent(descent_time, count)
        init.time.sleep(descent_time)
        count += 1
    start_photo_row(n_photo, len(coordinates), lenses[lens], len(coordinates), lens, id)
    return


def area(zone, lens, coverage):
    """
    Calculates the objective's paramaters matching the coverage required

    :param zone: objective's zone data
    :param lens: objective's lens
    :param coverage: objective's coverage needed
    :return: new lef and right borders, number of photo per row, y of the layers and time to acuire the objective
    """

    lenses = {'narrow': 550, 'normal': 750, 'wide': 950}
    t_y = {'narrow': 90, 'normal': 110, 'wide': 140}
    off = {'narrow': 586, 'normal': 786, 'wide': 986}
    coordinates = []

    #If the area crosses world map's vertical border
    if zone['left'] > zone['right']:
        distance = (int((21600 - zone['left'] + zone['right']) * coverage) // 2) + 1
        center = (zone['left'] + distance // 2) % 21600
    else:
        distance = (int((zone['right'] - zone['left']) * coverage) // 2) + 1
        center = (zone['left'] + zone['right']) // 2

    #Computing new left and right based on the coverage required
    new_left = int((center - distance) % 21600)
    new_right = int((center + distance) % 21600)

    #Calculating the number of photo needed for every row
    if (distance * 2) % lenses[lens] == 0:
        n_photo = (distance * 2) / lenses[lens]
    else:
        n_photo = ((distance * 2) // lenses[lens]) + 1

    #If the area crosses world map's horizontal border
    if zone['top'] > zone['bottom']:
        distance_y = (int((10800 - zone['top'] + zone['bottom']) * coverage) // 2) + 1
        center_y = (zone['top'] + distance_y // 2) % 10800
    else:
        distance_y = (int((zone['bottom'] - zone['top']) * coverage) // 2) + 1
        center_y = (zone['bottom'] + zone['top']) // 2

    #Computing new top and bottom based on the coverage required
    new_top = int((center_y - distance_y) % 10800)
    new_bottom = int((center_y + distance_y) % 10800)
    y_start = new_top + int(off[lens] / 2)
    offset = off[lens]

    #If new top and bottom crosses horizontal borders, recalculating objective's area height
    if new_bottom < new_top:
        pixel_size = 10800 - new_bottom + new_top
        lim_inf = 10800 + new_bottom
    else:
        pixel_size = new_bottom - new_top
        lim_inf = new_bottom

    pixel_size -= offset // 2
    coordinates.append(y_start)

    #Calculation of all layers y coordinates based on the area covered by the lens
    while lim_inf - y_start > ((lenses[lens] + 50) / 2):
        if pixel_size >= offset:
            pixel_size -= offset
        else:
            offset = pixel_size // 2

        y_start = (y_start + offset) % 10800

        if y_start < new_top:
            lim_inf = new_bottom
        coordinates.append(y_start)

    # Time expected to acquire the entire objective's area
    expected_t = ((distance // 5) + 1) * len(coordinates) + ((len(coordinates) - 1) * t_y[lens])
    return [new_left, new_right, n_photo, coordinates, expected_t]
