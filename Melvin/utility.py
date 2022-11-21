import init
import movement

def create_change_dir(id, response):
    """
    Creates new folder and set the working directory in it

    :param id: objective's id
    :param response: objective's data
    """

    dirname = '/obj/objective_' + str(id)

    if not init.os.path.exists(init.cur_dir + dirname):
        init.os.makedirs(init.cur_dir + dirname)

    json = open(init.cur_dir + dirname + '/params.json', 'w+')
    json.write(init.json.dumps(response))
    json.close()
    init.cd = init.cur_dir + dirname
    return


def compress_file(path):
    """
    Compress the specified file with .xz

    :param path:  path of the file
    """

    try:
        with open(path, "rb") as f:
            data = f.read()

        with init.lzma.open(path + ".xz", "w") as f:
            f.write(data)
    except:
        print("Error while compressing")



def convert_to_datetime(s, e):
    """
    Converts objective's start and end time to datetime

    :param s: start time
    :param e: end time
    :return: converted s and e
    """

    s = s.split('+')[0]
    s = init.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')
    e = e.split('+')[0]
    e = init.datetime.strptime(e, '%Y-%m-%dT%H:%M:%S')

    return [s, e]


def cruise_dec(x, y):
    """
    Manages all travel's phases (acceleration, cruise, deceleration)

    :param x: x velocity data
    :param y: y velocity data
    """

    if y[3] > x[3]:  #If y acceleration time is bigger than x acceleration time
        #Setting charge after y acceleration time
        init.sched.add_job(movement.cruise_charge, 'interval', seconds=y[3], id='cruisecharge', max_instances=1)
    else:
        # Setting charge after x acceleration time
        init.sched.add_job(movement.cruise_charge, 'interval', seconds=x[3], id='cruisecharge', max_instances=1)

    if y[3] + y[4] != 0:  #If no acceleration needed by the y
        init.sched.add_job(movement.f_dec_y, 'interval', seconds=y[3] + y[5], id='decy', max_instances=1)

    if x[3] + x[4] != 0: #If no acceleration needed by the x
        init.sched.add_job(movement.f_dec_x, 'interval', seconds=x[3] + x[5], id='decx', max_instances=1)

    if x[3] + x[4] == 0: #If only y requires deceleration
        init.sched.add_job(movement.charge, 'interval', seconds=y[1], id='charge', max_instances=1)
    return


def delta_time(e):
    """
    Calculates the seconds between current time and the input

    :param e: datetime value
    :return: difference in seconds
    """

    e = e.split('+')[0]
    e = init.datetime.strptime(e, '%Y-%m-%dT%H:%M:%S')
    s = init.datetime.now()
    return e - s


def take_photo(img, type, coordx='', coordy='', row='', map=False,mapwide = False,center = 0):
    """
    Saves the image taken by Melvin's camera

    :param mapwide: mapwide
    :param img: image data
    :param type: type of lens used
    :param coordx:
    :param coordy:
    :param row: row's number
    :param map: True if is a photo of the mapping
    """
    try:
        data = init.json.loads(init.requests.get(init.url + "observation").content)
        coordx = data['telemetry']['x']
        coordy = data['telemetry']['y']
        img_png = init.base64.b64decode(init.json.loads(img)['image'])
        img_np = init.np.frombuffer(img_png, dtype=init.np.uint8)
        img_cv = init.cv2.imdecode(img_np, flags=init.cv2.IMREAD_COLOR)

        if map is False:
            init.cv2.imwrite(init.os.path.join(init.cd, '|' + str(type) + '|' + str(row) + '|' + str(coordx) + "|" + str(
                coordy) + init.image_format), img_cv)
        else:
            init.cv2.imwrite(init.os.path.join(init.cur_dir + '/map','|' + str(type) + '|' + str(row) + '|' + str(coordx) + "|" + str(coordy) + init.image_format), img_cv)

            cover_zone(init.y_center, init.x_start, (center + 300) % 21600)

    except:
        print("Non sono riuscito a convertire la foto ( no active / troppo veloce)")
    return


def merge(intervals):
    """
    Merge all overlapping intervals

    :param intervals: intervals
    :return: merged intervals
    """

    intervals.sort(key=lambda a: a[0])  #Sort for start
    output = [intervals[0]]  #Edge cases

    for start, end in intervals:
        if output[-1][1] >= start:  #Overlap check the previous one this help for edge cases
            #And if we add we check the last one inside so we se all overlaps
            output[-1][0] = min(start, output[-1][0])
            output[-1][1] = max(end, output[-1][1])
        else:
            output.append([start, end])
    return output


def cover_zone(y_center, x_start=0, x_end=0):
    """
    Add the covered zone to the ones already scanned

    :param y_center: center of the photo
    :param x_start: left border of the area
    :param x_end: right border of the area
    """

    y_start = y_center - 300 if y_center - 300 > 0 else 10800 + (y_center - 300)
    y_end = (y_center + 300) % 10800

    if x_start > x_end: #If crosses the border splits the interval
        new_interval = [[0, x_end], [x_start, 21600]]
    else:
        new_interval = [[x_start, x_end]]

    tmp = None
    tmpmerge = []

    #Iterating all the y and computing the new merged interval only when founding an y that contains a different list of intervals
    for i in range(y_start, y_end):
        if init.y_scan[i] != tmp:
            tmp = init.y_scan[i]
            oldlist = []
            for x in init.y_scan[i]:
                oldlist.append(x)
            for x in new_interval:
                oldlist.append(x)
            tmpmerge = merge(oldlist)
            init.y_scan[i] = tmpmerge

        else:
            init.y_scan[i] = tmpmerge
    return


def watch_cover_zone(y_center):
    """
    Checks if the row, with center in y_center, has already been scanned

    :param y_center: center of the row
    :return: True if scanned
    """

    y_start = y_center - 300 if y_center - 300 > 0 else 10800 + (y_center - 300)
    y_end = (y_center + 300) % 10800
    for i in range(y_start, y_end + 1):
        if init.y_scan[i] != [[0, 21600]]:
            return False
    return True


def see_if_takephoto(y_center):
    """
    Find the common intervals, where photo have already been taken, between all the y starting from y_center

    :param y_center: starting y coordinate
    :return: list of common intervals
    """

    y_start = y_center - 300 if y_center - 300 > 0 else 10800 + (y_center - 300)
    y_end = (y_center + 300) % 10800

    tmp = None
    intervals = []
    for i in range(y_start, y_end):
        if init.y_scan[i] != tmp:

            tmp = init.y_scan[i]
            #If an x interval is empty, there are no common intervals between them, empty intersection
            if tmp == []:
                return []
            intervals.append(tmp)

    if len(intervals) == 0:
        return

    #If only one is founded returns it
    if len(intervals) == 1:
        return l[0]

    new = []
    for x in l[0]:
        new.append(x)

    for i in range(1, len(intervals)):
        temp_n = []
        for x in l[i]:
            for y in new:
                #All cases to check if there are common intervals
                if y[0] <= x[0] and x[1] <= y[1]:
                    temp_n.append(x)
                elif x[0] <= y[0] and y[1] <= x[1]:
                    temp_n.append(y)
                elif y[0] <= x[0] and y[1] <= x[1] and y[1] >= x[0]:
                    temp_n.append([x[0], y[1]])
                elif y[0] >= x[0] and y[1] >= x[1] and y[0] <= x[1]:
                    temp_n.append([y[0], x[1]])

        new = temp_n
    return new


def time_to_closest_y(curr):
    """
    Calculates the time to reach an uncompleted row from the current y

    :param curr: current y
    :return: time reach the row
    """

    start = -1
    for y in range(curr, 10800):
        if init.y_scan[y] != [[0, 21600]]:
            start = y
            break
    if start == -1:
        for y in range(0, curr):
            if init.y_scan[y] != [[0, 21600]]:
                start = y
                break

    #From the start descending at (10,1) velocity to the center (280px distant from the start, in order to have a 20px overlap) and then starting photographing
    center = start + 285
    if curr < center:
        time_to_descent = center - curr
    else:
        time_to_descent = (10800 - curr) + center

    return time_to_descent