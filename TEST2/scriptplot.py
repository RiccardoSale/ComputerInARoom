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
global value
scanx = 0
value = 100
sched = BlockingScheduler()

def color(x, y):
    global value
    for i in range(300):
        for j in range(300):
            matrix[(x + i)%10800][(y+j)%21600] = value
            if x-i < 0:
                matrix[ 10800 + (x - i)][(y+j)%21600] = value
            else:
                matrix[(x-i)][(y+j)%21600] = value
            matrix[(x+j)%10800][(y + i)%21600] = value
            if y-i < 0:
                matrix[(x+j)%10800][21600 + (y - i)] = value
            else:
                matrix[(x+j)%10800][y-i] = value
    



def plot():
    plt.matshow(matrix, fignum=100)
    plt.gca().set_aspect('auto')
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    plt.savefig(str(current_time)+'.png', dpi=600)

def scanning_orizontal():
    global scanx
    scanx += 1
    if scanx <= 36:
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
        cv2.imwrite(str(str(type_)+str(coordy)+"|"+str(coordx) + ".png"), img_cv)
        requests.put(url + "control", json={"state": 'charge', "camera_angle": 'narrow',"vel_x": 10, "vel_y": 0})
        color(coordy, coordx)  # remember to change x and y cord
        return
    if scanx == 37:
        global value
        value += 100
        sched.pause_job('scanning_orizontal')
        url = "http://192.168.5.2:11004/"
        requests.put(url + "control", json={"state": 'active', "camera_angle": 'narrow',"vel_x":10 , "vel_y": 1})
        response = requests.get(url + "observation").content
        print(response)
        time.sleep(595)
        requests.put(url + "control", json={"state": 'active', "camera_angle": 'narrow',"vel_x":10 , "vel_y": 0})
        response = requests.get(url + "observation").content
        print(response)
        scanx = 0
        sched.resume_job('scanning_orizontal')
        return

sched.add_job(scanning_orizontal, 'interval', seconds = 60 , id='scanning_orizontal', max_instances=50)
sched.add_job(plot,'interval', seconds = 43698 ,id='plot')
sched.start()
