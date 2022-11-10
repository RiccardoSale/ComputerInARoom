import base64
import json
import math
import os
from datetime import datetime
import time
import cv2
import numpy as np
import requests
from apscheduler.schedulers.blocking import BlockingScheduler

global active_objectives  # lista obbiettivi attivi
global taken  # Numero immagini scattate dal job photo
global vel_route
global real_vx  # velocità attuale reale
global real_vy
global the_tour
global t_photo
global scanx
global saved_obj
global data
global cd
global block
global url
global cur_dir
global y_scan
global x_scan
global x_start
global y_center
x_scan = []
x_start = 0
y_center = 0
block = False
cd = ''
saved_obj = {}
active_objectives = []
vel_route = []
scanx = 0
taken = 0
vel_route = 0
the_tour = 0
cur_dir = os.getcwd()
y_scan = {i: [] for i in range(10800)} #8027
sched = BlockingScheduler()

data = [
    {"id": 4, "name": "aurora_borealis", "start": "2022-11-10T13:30:00+00:00",
     "end": "2022-11-10T14:55:46+00:00",
     "done": False, "max_points": 6000, "decrease_rate": 0.9,
     "zone": {"left": 8000, "right": 10500, "top": 8000, "bottom": 9300}, "optic_required": "WIDE",
     "coverage_required": 100.0,
     "description": "An Aurora borealis is visible from space, can you ask MELVIN to take a picture of it for us please?"}
]

url = "http://192.168.5.2:11004/"
image_format = '.webp'

#fo
# r i in range(8027 - 300, 8027 + 300 + 1):
  #  y_scan[i] = [[0, 21600]]

#for i in range(8027 - 300, 8027 + 300 + 1):
 #   y_scan[i] = [[0, 5000]] if i <= 8027 else [[10000, 15000]]

# [0-8000]

# for i in range(8027 - 300, 8027 + 300 + 1):
#     if i <= 8027:
#         y_scan[i].append([16000, 17500])
#         y_scan[i].append([2500, 10000])
#     else:
#         if i == 8028:
#             y_scan[i].append([5000, 15000])
#             y_scan[i].append([16000, 20000])
#         else:
#             y_scan[i].append([4000, 11000])
#             y_scan[i].append([17000, 18000])

for i in range(8027 - 300, 8027 + 300 + 1):
    y_scan[i].append([0,1000])
