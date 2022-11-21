import os, cv2
import numpy as np
import sys
import json


def parse(fname):
    """
    parses the filename of the image to get the coordinates

    :param fname: filename on wich the parsing is executed
    :return: an array of coordinates [x,y]

    """
    step = fname.split('.')[0]
    info = step.split('|')
    coords = [info[3], info[4]]
    return coords


def load_json(mylist, path):
    """
    loads the values of the image from a provided .json file

    :param mylist: list of files where the json file is located
    :param path: absolute path of the .json file
    :return: an array containing the informations extracted from the .json file [output height, output width, offset, resize value (based on lens), objective name]

    """
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
    """
    used if no .json file is provided, loads default values

    :param mylist: list of files (used to find the lenses from the filenames)
    :param path: absolute path in wich the files are located
    :param h: height of the  output image
    :param w: width of the output image
    :return:  an array containing the informations [output height, output width, offset, resize value (based on lens), objective name]

    """
    print('loading default values...')
    offset = [0, 0]
    ho, wo = h, w
    dic = {'NARROW': 600, 'NORMAL' : 800, 'WIDE' : 1000}
    l = mylist[0].split('|')[1]
    r = dic[l]
    return [ho, wo, offset, r, l]


def stitch(p):
    """
    stitches the provided images into a single image of the desidered dimensions, it is the main function of the program.

    :param p: absolute path to the images

    """

    # creates a (h*2)x(w*2) image to use as a canvas, it is bigger to accomodate images that represent an area at the border
    h, w = 10800, 21600
    out = np.zeros((h * 2, w * 2, 3), np.uint8)

    try:
        path = p + '/'
        mylist = os.listdir(path)
    except:
        print('invalid arguments')
        sys.exit()

    # checks if a json file is present and initializes the stitching accordingly
    if 'params.json' in mylist:
        values = load_json(mylist, path)
    else:
        values = set_default(mylist, path, h, w)

    ho, wo, offset, r, l = values[0], values[1], [values[2][0], values[2][1]], values[3], values[4]


    for fname in mylist:

        #if the image is a webp image, adds it to the canvas according to its coordinates
        if fname.split('.')[1] == 'webp':
            coords = parse(fname)
            tmp = cv2.imread(path + fname)
            print('Image @ x: ' + coords[0] + ', y: ' + coords[1] + '... ')
            if r != 600:
                #if the image is taken with lens different from NORMAL, resizes it
                tmp = cv2.resize(tmp, (r, r), interpolation=cv2.INTER_LINEAR)
            y, x = int(int(coords[1]) + (h / 2)), int(int(coords[0]) + (w / 2))
            out[y: y + r, x: x + r] = tmp

            # if an image represents an area at the border (that has information on the opposite side of the image) pastes it at the opposite side too
            if x - w / 2 + r > w:
                out[y: y + r, x - w: x + r - w] = tmp
            if x - w / 2 - r < 0:
                out[y: y + r, x + w: x + r + w] = tmp
            if y - h / 2 + r > h:
                out[y - h: y + r - h, x: x + r] = tmp
            if y - h / 2 - r < 0:
                out[y + h: y + r + h, x: x + r] = tmp

    print('Saving...')
    # writes the images according to the input parameters
    cv2.imwrite(path + l + '.png', out[int(h / 2 + r / 2) + offset[0]: int(h / 2 + r / 2) + offset[0] + ho, int(w / 2 + r / 2)
                            + offset[1]: int(w / 2 + r / 2) + wo + offset[1]])
