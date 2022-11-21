import init
import stitching
import utility
import calculations
import mappingwide
import stitching

wide_path = '/home/user/melvin_unknown/mapwide'
unknown_wide_path = '/home/user/melvin_unknown/mapwideunknown'


def objectives():
    unknown_active = []  #List containing the json of active unknown objectives
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

                    elif x['id'] not in init.past_unknown: #Identified an unknown objective
                        unknown_active.append(x)

    if len(init.active_objectives) > 0:
        calculations.calculator()
        return

    #Wide scanning the map for the first time
    # there must be no active unknown objective while scanning, because this will be used for all future comparison
    elif init.first_time and len(unknown_active) == 0:
        init.first_time = False
        all_objectives.sort(key=lambda k: (k['done'] == 'False', k['start']), reverse=False)

        if len(all_objectives) != 0:
            next_date_obj = all_objectives[0]['start']  # Closest starting objective

            # Starting the scanning only if there's enough time to do it and to go to the next objective
            if (next_date_obj - now).total_seconds() > 5700 or all_objectives[0]['done'] == 'true':
                pause()
                start_date = init.datetime.now()
                end_date = init.timedelta(hours=1, minutes=28, seconds=0)

                init.sched.add_job(mappingwide.mappingwide, 'interval', seconds=14, start_date=start_date,
                                   end_date=end_date)
                init.time.wait(5400) #Wait the end of mapping wide job
                #Function reset needs to be edited and work with every velocity
                init.sched.add_job(reseset_wide, 'date', run_date=end_date)
                stitching.stitch(wide_path)
                return

    # Scanning the map whenever there's only one active unknown objective and having more than 1.5 hours from the start of another objective
    elif not init.first_time and len(unknown_active) == 1:
        unknown_zones = []
        all_objectives.sort(key=lambda k: (k['done'] == 'False', 'unknown' not in k['zone'], k['start']), reverse=False)

        for x in all_objectives:
            if x['done'] == 'False' and 'unknown' in x['zone']:
                #Not enough time for wide mapping, exiting
                if unknown_active[0] != x and (x['start'] - init.datetime.now()).total_seconds() < 5700:
                    return

        if len(all_objectives) != 0:
            next_date_obj = all_objectives[0]['start']

            if (next_date_obj - now).total_seconds() > 5700 or 'unknown' in all_objectives[0]['zone']:
                pause()
                start_date = init.datetime.now()
                end_date = init.timedelta(hours=1, minutes=28, seconds=0)

                init.sched.add_job(mappingwide.mappingwide, 'interval', seconds=14, start_date=start_date,
                                   end_date=end_date)
                init.time.wait(5400)
                init.sched.add_job(reseset_wide, 'date', run_date=end_date)

                stitching.stitch(unknown_wide_path)

                # Dividing both map in 4 parts to make the next operation lighter, in terms of space,
                # and saving their paths in a list
                splitted_1 = split_wide(wide_path)
                splitted_2 = split_wide(unknown_wide_path)

                # Comparing and saving the interval of the differences between the maps
                for i in range(len(splitted_1)):
                    unknown_zones.append(diff_and_range(splitted_1[i], splitted_2[i]))

                # Merging all intervals, in case the objective has been splitted
                merged = merge_zones(unknown_zones)
                unknown_zone = {"left": merged[0], "right": merged[1], "top": merged[2], "bottom": merged[3]}

                # Adding the unknown objective id to a list to avoid re-scanning in future
                x = unknown_active[0]
                init.past_unknown.append(x['id'])

                # Adding a custom objective with unknown objective's info and the interval found by the comparison
                custom_unknown = {"id": x['id'], "name": x['name'], "start": x['start'], "end": x['end'],
                                  "done": False, "max_points": x['max_points'], "decrease_rate": x['decrease_rate'],
                                  "zone": unknown_zone, "optic_required": x['optic_required'],
                                  "coverage_required": x['coverage_required'], "description": x['description']}

                #Custom objective will be recognized as a normal/known objective in the next job of this function and will be acquired
                init.data.append(custom_unknown)
                return
    return

def split_wide(path):
    """
    Divides the png of scanmap wide in 4 zone.

    :param path: path of the photo
    :return: list of paths of the 4 splitted images
    """

    PIL.Image.MAX_IMAGE_PIXELS = None
    paths = []
    img = imageio.imread_v2(path)
    name, extension = path.split('.')
    height, width, depth = img.shape

    #Vertical splitting
    width_cutoff = width // 4
    s1 = img[:, :width_cutoff]
    s2 = img[:,  width_cutoff:(width_cutoff * 2)]
    s3 = img[:, (width_cutoff * 2):(width_cutoff * 3)]
    s4 = img[:, (width_cutoff * 3):(width_cutoff * 4)]

    #Paths creation
    path_s1 = name + '_1.' + extension
    path_s2 = name + '_2.' + extension
    path_s3 = name + '_3.' + extension
    path_s4 = name + '_4.' + extension

    #Images saving
    imageio.imwrite(path_s1, s1)
    imageio.imwrite(path_s2, s2)
    imageio.imwrite(path_s3, s3)
    imageio.imwrite(path_s4, s4)

    paths.append(path_s1)
    paths.append(path_s2)
    paths.append(path_s3)
    paths.append(path_s4)

    return paths

def merge_zones(zones):
    """
    If an unknown object is beetween to splitted images i get more than one interval
    The function merge them

    :param zones: zones to merge
    :return: single zone merged
    """

    #Sums every left and right intervals
    zones_l = []
    for z in zones:
        zones_l.append(list(z))

    zone = []
    left = 21600
    right = 0

    #Fixing intervals
    for i, z in enumerate(zones_l):
        if len(z) != 0:
            z[0] += 5400 * i
            z[1] += 5400 * i


    for z in zones_l:
        if len(z) != 0:
            if z[0] < left:
                left = z[0]

            if z[1] > right:
                right = z[1]

            top = z[2]
            bot = z[3]

    if left == 0 and right == 21600:
        for z in zones_l:
            if len(z) != 0:
                if z[0] > left:
                    left = z[0]

                if z[1] < right:
                    right = z[1]

    zone.append(left)
    zone.append(right)
    zone.append(top)
    zone.append(bot)

    return zone



def diff_and_range(path_before,path_after):
    """
    Find the difference beetween two images.

    :param active_obj: active_objects array
    :param path_before: Map wide without unknown
    :param path_after: Map wide with one unknown object
    :return: Zone of the difference
    """

    img1 = cv2.imread(path_before)
    img2 = cv2.imread(path_after)
    diff = cv2.absdiff(img1, img2)
    mask = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    th = 1
    imask = mask > th
    canvas = np.zeros_like(img2, np.uint8)
    canvas[imask] = img2[imask]
    black = canvas[0, 0, :].astype(int)
    mask = cv2.inRange(canvas, black, black)

    #Once compared the new and old images a new one is created with white background and black pixel to higlight the differences
    cv2.imwrite("difference.png", mask)
    img = cv2.imread('difference.png')

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([0, 0, 0])

    black = cv2.inRange(hsv, lower_black, upper_black)

    cnts = cv2.findContours(black, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    unknown_obj = []

    #Finding the contours of all the black pixels area from the difference image
    for c in cnts:
        leftmost = tuple(c[c[:, :, 0].argmin()][0])
        rightmost = tuple(c[c[:, :, 0].argmax()][0])
        topmost = tuple(c[c[:, :, 1].argmin()][0])
        bottommost = tuple(c[c[:, :, 1].argmax()][0])
        cv2.drawContours(img, [c], -1, (0, 255, 0), 3)
        unknown_obj.append((leftmost[0], rightmost[0], topmost[1], bottommost[1]))

    final_unknown = []
    valid = True

    #Excluding from the calculations all the zone already covered by known objectives that could have modified the map
    for i, x in enumerate(unknown_obj):
        for elem in init.active_objectives:
            z = elem['zone']
            if z['left'] <= unknown_obj[i][0] and z['right'] >= unknown_obj[i][1] and z['top'] <= unknown_obj[i][2] and z['bottom'] >= unknown_obj[i][3]:
                valid = False

        if valid is True:
            final_unknown.append([unknown_obj[i][0], unknown_obj[i][1], unknown_obj[i][2], unknown_obj[i][3]])

        valid = True

    return final_unknown