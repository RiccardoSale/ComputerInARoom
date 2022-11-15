import os, cv2
import numpy as np
import sys
import json


def parse(fname):
    step = fname.split('.')[0]
    info = step.split('|')
    coords = [info[3], info[4]]
    return coords


def load_json(mylist, path):
    print('loading values from json...')
    with open(path + 'params.json', 'r') as f:
        parsed = json.load(f)

    offset = [parsed['zone']['top'], parsed['zone']['left']]
    ho, wo = int(parsed['zone']['bottom']) - int(parsed['zone']['top']), int(parsed['zone']['right']) - int(
        parsed['zone']['left'])

    print('final image will be: ' + 'height: ' + str(ho) + ' width: ' + str(wo))
    print('at offset' + ' y: ' + str(offset[0]) + ' x: ' + str(offset[1]))
    dic = {'NARROW': 600, 'NORMAL' : 800, 'WIDE' : 1000}
    r = dic[parsed['optic_required']]
    l = "objective_" + str(parsed['id'])

    for f in mylist:
        if f.split('.')[1] == 'json':
            mylist.remove(f)
    return [ho, wo, offset, r, l]


def set_default(mylist, path, h, w):
    print('loading default values...')
    offset = [0, 0]
    ho, wo = h, w
    dic = {'NARROW': 600, 'NORMAL' : 800, 'WIDE' : 1000}
    l = mylist[0].split('|')[1]
    r = dic[l]
    return [ho, wo, offset, r, l]


def stitch(p):
    h, w = 10800, 21600
    out = np.zeros((h * 2, w * 2, 3), np.uint8)

    try:
        path = p + '/'
        mylist = os.listdir(path)
    except:
        print('invalid arguments')
        sys.exit()

    if 'params.json' in mylist:
        values = load_json(mylist, path)
    else:
        values = set_default(mylist, path, h, w)

    ho, wo, offset, r, l = values[0], values[1], [values[2][0], values[2][1]], values[3], values[4]

    for fname in mylist:
        coords = parse(fname)
        tmp = cv2.imread(path + fname)
        print('Image @ ' + coords[1] + ':' + coords[0] + '... ')
        if r != 600:
            tmp = cv2.resize(tmp, (r, r), interpolation=cv2.INTER_LINEAR)
        y, x = int(int(coords[1]) + (h / 2)), int(int(coords[0]) + (w / 2))
        out[y: y + r, x: x + r] = tmp

        if x - w / 2 + r > w:
            out[y: y + r, x - w: x + r - w] = tmp
        if x - w / 2 - r < 0:
            out[y: y + r, x + w: x + r + w] = tmp
        if y - h / 2 + r > h:
            out[y - h: y + r - h, x: x + r] = tmp
        if x - h / 2 - r < 0:
            out[y + h: y + r + h, x: x + r] = tmp

    print('Saving...')
    cv2.imwrite(path + l + '.png', out[int(h / 2 + r / 2) + offset[0]: int(h / 2 + r / 2) + offset[0] + ho, int(w / 2 + r / 2)
                            + offset[1]: int(w / 2 + r / 2) + wo + offset[1]])
