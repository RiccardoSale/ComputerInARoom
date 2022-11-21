import init
import melvin
import objective_photo
import utility

TOTAL_X = 21600
TOTAL_Y = 10800

def calculator():
    """
    From the list of active objectives, calculate if one or more objectives are reachable,
    then call the function to reach the first (sorted by distance)

    With just one active objective and more than 1.5 hours till the end of it, wait and continue scan

    With multiple active objectives and more than 1.5 hours starts the travel to them

    If an objectives needs too much resources (fuel) due to short time

    """

    data = init.json.loads(init.requests.get(init.url + "observation").content)

    curr_x = int(data['telemetry']['vx'])  #Actual v_x
    curr_y = int(data['telemetry']['vy'])  #Actual v_y
    coord_x = int(data['telemetry']['x'])  #Actual x coord
    coord_y = int(data['telemetry']['y'])  #Actual y coord

    init.active_objectives.sort(key=lambda k: dist(coord_y, k['zone']['top'], TOTAL_Y), reverse=False)

    vel_arr = [[] for _ in range(len(init.active_objectives))] #List of velocity for each active objective
    init.vel_route = [0] * len(init.active_objectives) #Velocity chosen for the first objective
    t_route = 0 #Time of the travel
    count = 0
    limit = 20 #Max num of while's iterations, avoid to search more than 20 different velocity, 20 because it's hard to have more possible velocity for an objective
    t_photo_local = 0
    tp_first = 's' #Type of the first objective, 'm': multi-layer, 's':single-layer
    breaked = False
    data_first = None

    if dist(coord_y, init.active_objectives[0]['zone']['top'], 10800) < 300:
        print("Objective nearer than 300px, starting the travel")
        melvin.resume_the_tour()
        return

    while count <= limit:
        for objective, x in enumerate(init.active_objectives):
            #Retrieving objective's data
            zone = x['zone']
            final_x = zone['left']
            final_y = (zone['top'] + zone['bottom']) // 2
            lens = x['optic_required'].lower()
            x_end_target = zone['right']
            t_to_target = utility.delta_time(x['end'])
            t_to_target = int(int(t_to_target.total_seconds()) * 0.9) #Removing 10% of the available time to arrive at the objective in advance
            coverage = int(x['coverage_required']) / 100
            pixel_photo = ((zone['bottom'] - zone['top']) % 10800) * coverage #Pixels required to cover all the y area including the coverage required
            dic_limit = {'narrow': 550, 'normal': 750, 'wide': 950}

            if len(init.active_objectives) == 1 and t_to_target > 5400:
                print("Just one objective and more than 1.5 hours, continuing mapping")
                return

            if pixel_photo > dic_limit[lens]:  # multi-layer objective
                single_layer = False
                photo_data = objective_photo.area(zone, lens, coverage)

                if x == init.active_objectives[0]:
                    data_first = photo_data
                    tp_first = 'm'

                expected_t = photo_data[4]
                t_to_target -= expected_t

            else:
                dist_ = dist(final_x, x_end_target, 21600)

                if dist_ % 10 == 0:
                    t_photo_local = dist_ / 10
                else:
                    t_photo_local = (dist_ // 10) + 1
                if x == init.active_objectives[0]:
                    init.t_photo = t_photo_local

                single_layer = True
                t_to_target -= t_photo_local

            t_to_target -= t_route
            #Subtracting from t_to_target the time to take the photos and the travel's time

            if t_to_target < 150: #Avoiding expensive velocities in terms of fuel, 150 equals 2.50 minutes which comports uncovenient change of speed
                breaked = True
                break

            res = calculate_distance_time_fuel(final_x, final_y, t_to_target, curr_x, curr_y, coord_x, coord_y, multiple=True) \
                if single_layer is True else calculate_distance_time_fuel(photo_data[0], photo_data[3][0], t_to_target, curr_x, curr_y, coord_x, coord_y, multiple=True)

            if len(res) == 0:
                print("Res empty, objective unreachable with current velocity, trying faster one")
                breaked = True
                break

            vel_arr[objective] = res
            init.vel_route[objective] = max(len(res)-1,count)

            if single_layer: #Adding to t_route the travel'stime and photo's time
                t_route += vel_arr[objective][max(len(res)-1,count)][0][1] + t_photo_local
            else:
                t_route += vel_arr[objective][max(len(res)-1,count)][0][1] + expected_t

            coord_x = final_x
            coord_y = final_y

        if breaked is False:
            if tp_first == 's':
                print("Starting single-layer objective")
                melvin.go_and_scan(vel_arr[0][count][0], vel_arr[0][count][1],
                                   init.active_objectives[0]['optic_required'].lower(),
                                   init.active_objectives[0]['id'], init.active_objectives[0])
            else:
                print("Starting multi-layer objective")
                melvin.go_and_scan(vel_arr[0][count][0], vel_arr[0][count][1],
                                   init.active_objectives[0]['optic_required'].lower(),
                                   init.active_objectives[0]['id'], init.active_objectives[0], data_first[3],
                                   data_first[2], True)
            return
        else:
            # Restoring original values
            curr_x = int(data['telemetry']['vx'])  # vx attuale
            curr_y = int(data['telemetry']['vy'])  # vy attuale
            coord_y = int(data['telemetry']['y'])
            coord_x = int(data['telemetry']['x'])
            vel_arr = [[] for _ in range(len(init.active_objectives))]
            breaked = False
            count += 1
            t_route = 0

    print("Starting the nearest")
    melvin.resume_the_tour()
    return


def dist(one, two, module=1):
    """
    Distance in pixel between 2 coordinates

    :param one: first coordinate
    :param two: second coordinate
    :param module: module to apply
    :return:
    """
    return two - one % module if module != 1 else two - one


def f_min_xy(value):
    """
    Find the minimun velocity for x / y given the actual velocity of y / x

    :param value: current velocity x / y
    :return: minimum velocity y / x
    """
    if value > 3:
        return 1
    else:
        return 1 if 10 - pow(value, 2) < 0 else init.math.trunc(init.math.sqrt(10 - pow(value, 2))) + 1


def filter_matrix(m):
    """
    Removes 0 values from the velocity's matrix

    :param m: velocity's matrix
    :return: filtered matrix
    """
    for i in range(len(m) - 1, 0, -1):
        aux = m[i]
        if m[i][2] == 0: m.remove(aux)
    return m


def generate(tp, max, min, curr, dec, t_to_target, delta, m, negative, multiple=False):
    """
    Determines all the possible velocities for x or y to reach a specific point in the map on time

    :param tp: type of velocity, x or y
    :param max: maximum velocity
    :param min: minimum velocity
    :param curr: current velocity
    :param dec: final velocity to reach
    :param t_to_target: time to reach the destination
    :param delta: difference in pixel between current position and destination
    :param m: empty matrix of speed
    :param negative: allows negative velocities
    :param multiple: enables the return of all the velocities instead of the minimum
    :return: matrix of the velocities
    """
    for i in range(0, max - min + 1, 1):
        cand = int(min + i) #Current candidate velocity

        if (cand < curr): #Decelerating speed
            p_dec_1 = (((curr + cand + 1) / 2) * (curr - dec + 2)) + (
                    ((curr - 1 + cand) / 2) * (curr - cand)) + (0.5 * (curr - cand))  #Pixels covered in first deceleration
            p_dec_2 = (((cand + dec + 1) / 2) * (cand - dec + 2)) + (
                    ((cand - 1 + dec) / 2) * (cand - dec)) + (0.5 * (cand - dec))  #Pixels covered in second deceleration
            t_dec_1 = 2 * abs(curr - cand) #First deceleration time
            t_dec_2 = 2 * abs(cand - dec) #Second deceleration time
            t_mov = t_dec_1 + t_dec_2 #Total deceleration time
            p_mov = p_dec_1 + p_dec_2 #Pixel covered in deceleration
            t_acc = t_dec_1
            t_dec = t_dec_2

            if p_mov > abs(delta): #Deceleration pixel bigger than the distance of the route
                continue
        if cand > curr: #Accelerating speed
            p_acc = 2 * (((curr + cand - 1) / 2) * (cand - curr)) + (0.5 * (cand - curr)) #Pixels covered in acecleretion
            p_dec = (((cand + dec + 1) / 2) * (cand - dec + 2)) + (((cand - 1 + dec) / 2) * (cand - dec)) + (0.5 * (cand - dec)) #Pixels covered in deceleration
            t_acc = 2 * abs(cand - curr) #Acceleration time
            t_dec = 2 * abs(cand - dec) #Deceleration time
            t_mov = t_acc + t_dec
            p_mov = p_acc + p_dec
            if (p_acc + p_dec) > abs(delta): #Acceleration and deceleration covering more pixel than the route
                break
        if cand == curr: #Canditate mathces current velocity
            t_acc = t_dec = t_mov = p_mov = 0
        fuel = init.math.sqrt((pow(cand - curr, 2))) / 100 + init.math.sqrt(
            (pow(cand - dec, 2))) / 100  #Fuel consumption

        if delta >= 0:
            cruise = delta - p_mov #Cruise pixels
        else: #Travelling across image's borders
            if tp == 'x':
                cruise = 21600 - abs(delta) - p_mov
            else:
                cruise = 10800 - abs(delta) - p_mov

        t_cruise = abs(int(cruise / cand))  #Cruising time
        t_tot = (t_cruise + t_mov) #Total travel's time

        if t_tot <= t_to_target: #Valid speed candidate
            if tp == 'x':
                m.append([cand, t_tot, int(fuel * 100) / 100, t_acc, t_dec, t_cruise])
                if multiple is False:
                    return m
            else:
                if negative: #Including negative y_velocities
                    if delta < 0:
                        m.append([cand, t_tot, int(fuel * 100) / 100, t_acc, t_dec, t_cruise])
                    else:
                        m.append([-cand, t_tot, int(fuel * 100) / 100, t_acc, t_dec, t_cruise])
                else:
                    m.append([cand, t_tot, int(fuel * 100) / 100, t_acc, t_dec, t_cruise])

    m = filter_matrix(m)
    return m



def calculate_distance_time_fuel(final_x, final_y, t_to_target, curr_x, curr_y, coord_x, coord_y, multiple=False):
    """
    Calculate all the velocities and their data (fuel consumption, travel time, acceleration time, deceleration time, cruise time)

    :param final_x: x position of the target
    :param final_y: y position of the target
    :param t_to_target: time to reach the destination
    :param curr_x: current x velocity
    :param curr_y: current y velocity
    :param coord_x: current x position
    :param coord_y: current y position
    :param multiple: enables the return of all the velocities instead of the minimum
    :return: list of all possible velocities [x,y] to reach the destination
    """
    dec_y = 0
    dec_x = 10
    init.real_vx = curr_x
    init.real_vy = curr_y

    min_y = f_min_xy(curr_x) #Min y velocity possible given actual v_x
    min_x = 10

    max_y = init.math.trunc(init.math.sqrt(4900 - pow(curr_x, 2)))  #Max y velocity possible given actual v_x
    max_x = init.math.trunc(init.math.sqrt(4900 - pow(curr_y, 2)))  #Max x velocity possible given actual v_y

    delta_y = dist(coord_y, final_y) #Pixels distance between current and target y coordinates
    delta_x = dist(coord_x, final_x) #Pixels distance between current and target x coordinates

    m_vel_y = []
    m_vel_x = []
    m_vel_y2 = []
    m_multiple = []
    m_vel_x = generate('x', max_x, min_x, curr_x, dec_x, t_to_target, delta_x, m_vel_x, False, multiple)
    negative = True if coord_y > final_y else False

    if (abs(final_y - coord_y) % 10800) < 4:
        print("Current y almost matches objective's y, nearer than 4px")
        list_y = [[0, 0, 0, 0, 0, 0]]
    else:
        m_vel_y = generate('y', max_y, min_y, curr_y, dec_y, t_to_target, delta_y, m_vel_y, negative, multiple)
        m_vel_y2 = generate('y', max_y, min_y, curr_y, dec_y, t_to_target, - delta_y, m_vel_y2, negative, multiple)
        list_y = m_vel_y + m_vel_y2
        list_y.sort(key=lambda el: el[2])

    if multiple: #Returning all possible pair of (x,y) velocity
        for x in m_vel_x:
            for y in list_y:
                if y[1] < x[1]:
                    m_multiple.append([x, y])
                    break
        return m_multiple

    x = m_vel_x[0]
    for i in list_y: #Calculates the least expensive pair of (x,y) velocity
        if i[1] < x[1]:
            y = i
            break

    return [x, y]
