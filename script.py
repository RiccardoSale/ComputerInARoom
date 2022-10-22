import base64
import json
import numpy as np
import requests as requests
import matplotlib.pylab as plt
import cv2
from datetime import datetime
from apscheduler.schedulers.background import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import time

np.set_printoptions(edgeitems=1000, linewidth=100000,formatter=dict(float=lambda x: "%.5g" % x))
matrix = np.zeros((10800, 21600))
global scanx
scanx = 0
sched = BlockingScheduler()

def color(x, y):
    for i in range(300):
        matrix[(x + i)%10800][y] = 25
        if x-i < 0:
            matrix[ 10800 + (x - i)][y] = 25
        else:
            matrix[(x-i)][y] = 25
        matrix[x][(y + i)%21600] = 25
        if y-i < 0:
            matrix[x][21600 + (y - i)] = 25
        else:
            matrix[x][y-i] = 25



def plot():
    plt.matshow(matrix, fignum=100)
    plt.gca().set_aspect('auto')
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    plt.savefig(str(current_time)+'.png', dpi=600)

def scanning_orizontal():
    global scanx
    scanx += 1
    if scanx <= 2:
        url = "http://192.168.5.2:11004/"
        requests.put(url + "control", json={"state": 'active', "camera_angle": 'narrow',"vel_x": 10 , "vel_y": 0})
        response = requests.get(url + "observation").content
        print(response)
        data = json.loads(response)
        coordx = data['telemetry']['x']
        coordy = data['telemetry']['y']
        type_ = data['telemetry']['angle']
        response = requests.get(url + "image").content
        img_png = base64.b64decode(json.loads(response)['image'])
        img_np = np.frombuffer(img_png, dtype=np.uint8)
        img_cv = cv2.imdecode(img_np, flags=cv2.IMREAD_COLOR)
        cv2.imwrite(str(str(type_)+str(coordx)+"|"+str(coordy) + ".png"), img_cv)
        requests.put(url + "control", json={"state": 'charge', "camera_angle": 'narrow',"vel_x": 10, "vel_y": 0})
        color(coordy, coordx)  # remember to change x and y cord
        return
    if scanx == 3:
        print("comincio a scendere")
        scanx = 4
        sched.pause_job('scanning_orizontal')
        url = "http://192.168.5.2:11004/"
        requests.put(url + "control", json={"state": 'active', "camera_angle": 'narrow',"vel_x":10 , "vel_y": 1})
        response = requests.get(url + "observation").content
        print(response)
        time.sleep(59)
        requests.put(url + "control", json={"state": 'active', "camera_angle": 'narrow',"vel_x":10 , "vel_y": 0})
        response = requests.get(url + "observation").content
        print(response)
        scanx = 0
        sched.resume_job('scanning_orizontal')
        return

sched.add_job(scanning_orizontal, 'interval', seconds = 10 , id='scanning_orizontal', max_instances=50)
sched.add_job(plot,'interval', seconds = 49698 ,id='plot')
sched.start()
