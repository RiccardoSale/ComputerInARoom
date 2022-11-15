import init
import movement


def create_change_dir(id,response):
    dirname = '/obj/objective_' + str(id)

    if not init.os.path.exists(init.cur_dir + dirname):
        init.os.makedirs(init.cur_dir + dirname)

    json = open(init.cur_dir+dirname+'/params.json', 'w+')
    json.write(init.json.dumps(response))
    json.close()
    init.cd = init.cur_dir + dirname
    return

def convert_to_datetime(s, e):
    s = s.split('+')[0]
    s = init.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')
    e = e.split('+')[0]
    e = init.datetime.strptime(e, '%Y-%m-%dT%H:%M:%S')

    return [s, e]


def cruise_dec(x, y):
    print("cruise decel")
    if y[3] > x[3]:  # Se tempo di accelerazione dell y è maggiore
        print("Y", y[3], y[5], init.datetime.now())
        init.sched.add_job(movement.cruise_charge, 'interval', seconds=y[3], id='cruisecharge', max_instances=1)
    else:
        init.sched.add_job(movement.cruise_charge, 'interval', seconds=x[3], id='cruisecharge', max_instances=1)

    if y[3] + y[4] != 0:
        init.sched.add_job(movement.f_dec_y, 'interval', seconds=y[3] + y[5], id='decy', max_instances=1)

    if x[3] + x[4] != 0:
        init.sched.add_job(movement.f_dec_x, 'interval', seconds=x[3] + x[5], id='decx', max_instances=1)

    print(x[3] + x[4])
    if x[3] + x[4] == 0:  # caso y che decelera e x ferma
        print("caso y decelera e ferma")
        init.sched.add_job(movement.charge, 'interval', seconds=y[1], id='charge',
                           max_instances=1)  # todo chiamare start cruise
    return

def delta_time(e):
    e = e.split('+')[0]
    e = init.datetime.strptime(e, '%Y-%m-%dT%H:%M:%S')
    s = init.datetime.now()
    return e - s


def take_photo(img, type, coordx='', coordy='', row='', map=False):
    response = init.requests.get(init.url + "observation").content
    data = init.json.loads(response)
    coordx = data['telemetry']['x']
    coordy = data['telemetry']['y']
    print("take Faccio foto")
    img_png = init.base64.b64decode(init.json.loads(img)['image'])
    img_np = init.np.frombuffer(img_png, dtype=init.np.uint8)
    img_cv = init.cv2.imdecode(img_np, flags=init.cv2.IMREAD_COLOR)
    print(init.cd)
    if map is False:
        init.cv2.imwrite(init.os.path.join(init.cd, '|' + str(type) + '|' + str(row) + '|' + str(coordx) + "|" + str(
            coordy) + init.image_format), img_cv)
    else:
        init.cv2.imwrite(init.os.path.join(init.cur_dir + '/map',
                                           '|' + str(type) + '|' + str(row) + '|' + str(coordx) + "|" + str(
                                               coordy) + init.image_format), img_cv)
    return

def merge(intervals):
    intervals.sort(key=lambda a: a[0])  # sort for start
    output = [intervals[0]]  # edge cases

    for start, end in intervals:
        if output[-1][1] >= start:  # overlap check the previous one this help for edge cases
            # and if we add we check the last one inside so we se all overlaps
            output[-1][0] = min(start, output[-1][0])
            output[-1][1] = max(end, output[-1][1])
        else:
            output.append([start, end])
    return output


def cover_zone(y_center, x_start=0, x_end=0):
    y_start = y_center - 300 if y_center - 300 > 0 else 10800 + (y_center - 300)
    y_end = (y_center + 300) % 10800

    if x_start > x_end:
        new_interval = [[0, x_end], [x_start, 21600]] 
    else:
        new_interval = [[x_start, x_end]]

    tmp = None
    tmpmerge = []
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
    y_start = y_center - 300 if y_center - 300 > 0 else 10800 + (y_center - 300)
    y_end = (y_center + 300) % 10800
    for i in range(y_start, y_end + 1):
        if init.y_scan[i] != [[0, 21600]]:
            return False
    return True

def see_if_takephoto(y_center):
    y_start = y_center - 300 if y_center - 300 > 0 else 10800 + (y_center - 300)
    y_end = (y_center + 300) % 10800

    tmp = None
    l = []
    for i in range(y_start, y_end):
        if init.y_scan[i] != tmp:

            tmp = init.y_scan[i]
            if tmp == []:
                return []
            l.append(tmp)
    if len(l) == 0:
        print("la lista di controllo dell intervallo è vuota")
        return
    if len(l) == 1:  # ho un unico intervallo posso returnare quello #TODO CONTROLLARE
        return l[0]  # vedere se funzia tramite pop

    new = []
    for x in l[0]:
        new.append(x)
    for i in range(1, len(l)):
        temp_n = []
        for x in l[i]:
            for y in new:
                print("x", x)
                print("y", y)
                if y[0] <= x[0] and x[1] <= y[1]:
                    temp_n.append(x)
                elif x[0] <= y[0] and y[1] <= x[1]:
                    temp_n.append(y)
                elif y[0] <= x[0] and y[1] <= x[1] and y[1] >= x[0]:
                    temp_n.append([x[0], y[1]])
                elif y[0] >= x[0] and y[1] >= x[1] and y[0] <= x[1]:
                    temp_n.append([y[0], x[1]])
                print("tttt",temp_n)

        new = temp_n
    print("NEW: ", new)
    return new


def time_to_closest_y(curr):
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
    print('START: ', start)
    #da start scendiamo a velocita' (10, 1) fino a center (dista dallo start di 280px, cosi' da avere un overlap di 20px)
    #poi iniziamo a fotografare da li
    center = start + 285
    if curr < center:
        t = center - curr #tempo per andare da curr a center (start + shift 280px)
    else:
        t = (10800 - curr) + center #tempo per arrivare alla fine + tempo per andare a center (start + shift 280px)

    return t
