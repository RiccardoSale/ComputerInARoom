#!/usr/bin/env python3
import base64
import cv2
import sys
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import json
import requests
import glob, os
console = True

def color(x, y):
    if x - 300 < 0:
        coordx = 10800 - x
    else:
        coordx = x - 300
    if y - 300 < 0:
        coordy = 21600 - y
    else:
        coordy = y - 300
    for i in range(600):
        for j in range(600):
            matrix[(coordx + i) % 10800][(coordy + j) % 21600] += 100
while console:
    var = input("Please enter the command: ")
    print("You entered: " + var)
    url_console_command = "http://192.168.5.2:12004/"
    url_Melvin_command = "http://192.168.5.2:11004/"
    if var == "book":
        id_ = input("Please enter the id for the booking (integer)")
        active = input("Please enter the active status (integer)")
        response = requests.put(url_console_command+"slots", json={"id": int(id_), "active": int(active)})
        print(response.json())
    if var == "simulation":
        activate_network_simulation = input("Please choose to activate network simulation (integer)")
        world_id = input("Please enter world id")
        reset = input("Please choose reset 0/1")
        response = requests.put(url_console_command + "simulation",
                                json={"activate_network_simulation": int(activate_network_simulation),
                                      "set_world_id": int(world_id),
                                      "reset": int(reset)})
        print(response.json())
    if var == "send":
        name = input("Please enter name of the image to send")
        img = cv2.imread('prova.png')
        _, im_arr = cv2.imencode('.png', img)  # im_arr: image in Numpy one-dim array format.
        im_bytes = im_arr.tobytes()
        im_b64 = base64.b64encode(im_bytes)

        #we need to find the last event_number we have completed with that photo
        #event_number =
        #we also need the image in cv2 base64 encoding
        #request.put( url_console_command + "send" , json={“event_number” : int(event_number), “picture”: im_b64}
        
        
        
    if var  == "reset":
        response = requests.put(url_Melvin_command + "reset")
        print("Reset sent!")
        print("Response received:")
        print(response.json())
    if var  == "observation_loop":
        while True:
            response = requests.get(url_Melvin_command + "observation").content
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            print("Current Time:", current_time)
            print("Response received:")
            print(response)
            data = json.loads(response)
    if var == 'obj':
        print("waiting for vpn")
        response = requests.get(url_Melvin_command + "objectives").content
        data = json.loads(response)
        data = data['objectives']
        lines = []
        for x in data:
            lines.append(x)
        lines.sort(key= lambda k: k['start'], reverse= False)
        now = datetime.now()

        active = []  #futuro array per obbiettivi multipli e far conti distanze
        for x in lines:#filtriamo obbiettivi e prendiamo solo quelli attivi e che non abbiamo completato
            if not x['done']:
                s = x['start']
                e = x['end']
                s = s.split('+')[0]
                s = datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')
                e = e.split('+')[0]
                e = datetime.strptime(e, '%Y-%m-%dT%H:%M:%S')
                if s <= now <= e:
                    active.append(x)
        
        
    if var == "observation":
        print("waiting for vpn")
        response = requests.get(url_Melvin_command + "observation").content
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print("Current Time:", current_time)
        print("Response received:")
        print(response)
        data = json.loads(response)
    if var == "switchtocharge":
        print("waiting for vpn")
        response = requests.get(url_Melvin_command + "observation").content
        data = json.loads(response)
        vel_x = data['telemetry']['vx']
        vel_y = data['telemetry']['vy']
        camera_angle = data['telemetry']['angle']
        requests.put(url_Melvin_command + "control",
                     json={"state": 'charge',
                           "camera_angle": camera_angle,
                           "vel_x": vel_x, "vel_y": vel_y})
        print("Switch to charge done")
    if var == "switchtoactive":
        print("waiting for vpn")
        response = requests.get(url_Melvin_command + "observation").content
        data = json.loads(response)
        vel_x = data['telemetry']['vx']
        vel_y = data['telemetry']['vy']
        camera_angle = data['telemetry']['angle']
        requests.put(url_Melvin_command + "control",
                     json={"state": 'active',
                           "camera_angle": camera_angle,
                           "vel_x": vel_x, "vel_y": vel_y})
        print("Switch to active done")

    if var == "changevel":
        print("waiting for vpn")
        response = requests.get(url_Melvin_command + "observation").content
        vel_x = input("Please enter vel_x")
        vel_y = input("Please enter vel_y")
        data = json.loads(response)
        state = data['telemetry']['state']
        camera_angle = data['telemetry']['angle']
        requests.put(url_Melvin_command + "control",
                     json={"state": state ,
                           "camera_angle": camera_angle,
                           "vel_x": vel_x, "vel_y": vel_y})
        print("Switch vel done")

    if var == "switchcamera_angle":
        response = requests.get(url_Melvin_command + "observation").content
        data = json.loads(response)
        camera_angle = input("Please enter camera angle")
        state = data['telemetry']['state']
        vel_x = data['telemetry']['vx']
        vel_y = data['telemetry']['vy']
        requests.put(url_Melvin_command + "control",
                     json={"state": state,
                           "camera_angle": camera_angle,
                           "vel_x": vel_x, "vel_y": vel_y})
        print("Switch camera_angle done")

    if var == "image":
        response = requests.get(url_Melvin_command + "image").content
        img_png = base64.b64decode(json.loads(response)['image'])
        img_np = np.frombuffer(img_png, dtype=np.uint8)
        img_cv = cv2.imdecode(img_np, flags=cv2.IMREAD_COLOR)
        cv2.imwrite(str(sys.argv[2] + ".png"), img_cv)
    
    if var == "plot":
        print("Start plotting")
        np.set_printoptions(edgeitems=1000, linewidth=100000, formatter=dict(float=lambda x: "%.5g" % x))
        matrix = np.zeros((10800, 21600))
        directory = os.getcwd()
        os.chdir(directory)
        csv = open('coords.csv','w+')

        for f in glob.glob("*.png"):
            if 'matrix' not in f:
                f = f[6:]
                f = f.replace('.png','')
                x,y = f.split('|')   
                csv.write(x+','+y+'\n')

        csv.close()
        f = open('coords.csv')
        lines = f.readlines()
        for line in lines:
            coords = line.split(',')
            color(int(coords[0]), int(coords[1]))
        
        f.close()
        plt.imshow(matrix, cmap='gist_stern')
        plt.colorbar()
        plt.gca().set_aspect('auto')
        plt.savefig('matrix', dpi=600)

    if var == "stiching":
        print('Start stiching')
        out = np.zeros((21600,43200,3), np.uint8)
        path = os.getcwd()
        path += '/'
        mylist = os.listdir(path)
        for fname in mylist:
            if 'NARROW' in fname:
                step = fname.split('.')[0]
                step = step.split('NARROW')[1]
                coords = step.split('|')
                tmp = cv2.imread(path + fname)
                y,x= int(coords[1])+5400, int(coords[0])+10800
                out[y: y + 600, x: x + 600 ] = tmp
        cv2.imwrite('map.png',out[5000 : 5000 + 12000, 10000 : 10000 + 24000])
        
    if var == "exit":
        print("Console will be terminated")
        console = False
