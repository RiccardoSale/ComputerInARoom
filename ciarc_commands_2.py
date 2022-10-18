#!/usr/bin/env python3
import base64
import json
import cv2
import requests
import sys
import numpy as np
from datetime import datetime


if len(sys.argv) > 1:  # Check if arguments were sent to the function (+1 everytime)
    if str(sys.argv[1]) == str("book") and len(sys.argv) == 4:
        url = "http://192.168.5.2:12004/"
        response = requests.put(url + "slots", json={"id": int(sys.argv[2]), "active": int(sys.argv[3])})
        print("Response received:")
        print(response.json())
    elif str(sys.argv[1]) == "simulation" and len(sys.argv) == 5:
        url = "http://192.168.5.2:12004/"
        response = requests.put(url + "simulation",
                                json={"activate_network_simulation": int(sys.argv[2]), "set_world_id": int(sys.argv[3]),
                                      "reset":
                                          int(sys.argv[4])})
        print("Response received:")
        print(response.json())

    elif str(sys.argv[1]) == "reset":
        url = "http://192.168.5.2:11004/"
        # response = requests.put(url + "reset", {"active": int(1)})
        response = requests.put(url + "reset")
        print("Reset sent!")
        print("Response received:")
        print(response.json())

    elif str(sys.argv[1]) == "control" and len(sys.argv) == 6:
        url = "http://192.168.5.2:11004/"
        if sys.argv[2] == "idle" or sys.argv[2] == "active" or sys.argv[2] == "charge":
            if sys.argv[3] == "narrow" or sys.argv[3] == "normal" or sys.argv[3] == "wide":
                response = requests.put(url + "control", json={"state": sys.argv[2], "camera_angle": sys.argv[3],
                                                               "vel_x": sys.argv[4], "vel_y": sys.argv[5]})
                print("Response received:")
                print(response.json())
            else:
                print("Wrong angle provided for the camera, received:" + str(
                    sys.argv[3] + " should be narrow normal or wide"))
        else:
            print("Wrong state provided for MELVIN, received:" + str(sys.argv[2] + " should be idle active or charge"))
    elif str(sys.argv[1]) == "observation" and len(sys.argv) == 2:
        url = "http://192.168.5.2:11004/"
        response = requests.get(url + "observation").content
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print("Current Time:",current_time)
        print("Response received:")
        print(response)
    elif str(sys.argv[1]) == "image":
        if len(sys.argv) == 3:

            url = "http://192.168.5.2:11004/"

            response = requests.put(url + "control", json={"state": 'active', "camera_angle": 'normal',
                                                           "vel_x": 70, "vel_y": 3})
            print(response)
            print("----------------------------------------------------------------")
            response = requests.get(url + "observation").content
            data = json.loads(response)
            coordx = data['telemetry']['x']
            coordy = data['telemetry']['y']
            type_ = data['telemetry']['angle']
            print(response)
            print("----------------------------------------------------------------")
            response = requests.get(url + "image").content
            img_png = base64.b64decode(json.loads(response)['image'])
            img_np = np.frombuffer(img_png, dtype=np.uint8)
            img_cv = cv2.imdecode(img_np, flags=cv2.IMREAD_COLOR)
            cv2.imwrite(str(str(type_)+str(coordx)+"|"+str(coordy) + ".png"), img_cv)
            response = requests.put(url + "control", json={"state": 'charge', "camera_angle": 'normal',
                                                           "vel_x": 70, "vel_y": 3})
            print(response)
            print("----------------------------------------------------------------")

        else:
            print("To get an image you should simplify the name of the picture")
    else:
        print("Argument not found")
        print("You can send the following commands:")
        print("reset                                            - To reset the simulation")
        print("book [id] [1/0]                                  - To book or cancel a specific pass")
        print(
            "simulation [1/0] [set_world_id] [1/0]            - To enable or disable network simulation, set the world")
        print("Id, and reset the simulation")
        print("control [state] [camera_angle] [vel_x] [vel_y]   - To change the MELVIN state: idle, active or charge")
        print("image [name of the picture without extension]    - To take a picture with MELVIN camera")
        print("End of available commands")
else:  # If no launch arguments were provided, inform the user of possible arguments
    print("No arguments provided")
    print("You can send the following commands:")
    print("reset                                            - To reset the simulation")
    print("book [id] [1/0]                                  - To book or cancel a specific pass")
    print("simulation [1/0] [set_world_id] [1/0]            - To enable or disable network simulation, set the world")
    print("Id, and reset the simulation")
    print("control [state] [camera_angle] [vel_x] [vel_y]   - To change the MELVIN state: idle, active or charge")
    print("image [name of the picture without extension]    - To take a picture with MELVIN camera")
    print("End of available commands")
