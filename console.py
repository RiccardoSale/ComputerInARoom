#!/usr/bin/env python3
import base64
import cv2
import sys
import numpy as np
from datetime import datetime
import json
import requests
console = True
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
        input("Please enter name of the image to send")
        #we need to find the last event_number we have completed with that photo
        #event_number =
        #we also need the image in cv2 base64 encoding
        #request.put( url_console_command + "send" , json={“event_number” : int(event_number), “picture”: base64}
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
    if var == "observation":
        response = requests.get(url_Melvin_command + "observation").content
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print("Current Time:", current_time)
        print("Response received:")
        print(response)
        data = json.loads(response)
    if var == "switch_tocharge":
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
    if var == "change_vel":
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

    if var == "switch_camera_angle":
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
    if var == "exit":
        print("Console will be terminated")
        console = False
