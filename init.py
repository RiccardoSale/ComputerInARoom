import base64
import json
import math
import os
from datetime import datetime , timedelta
import time
import cv2
import numpy as np
import requests
import json
import shutil
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
global x_start
global y_center

x_start = 0
y_center = 0
block = False
cd = ''
saved_obj = {}
active_objectives = []
vel_route = []
scanx = 0
taken = 0
the_tour = 0
cur_dir = os.getcwd()
y_scan = {i: [] for i in range(10800)} #8027

global wide_scanx
wide_scanx = 0


sched = BlockingScheduler()

data = [
    {"id": 21, "name": "aurora_borealis", "start": "2022-11-15T01:20:00+00:00",
     "end": "2022-11-15T02:53:46+00:00",
     "done": 'false', "max_points": 6000, "decrease_rate": 0.9,
     "zone": {"left": 8000, "right": 10500, "top": 8000, "bottom": 9300}, "optic_required": "WIDE",
     "coverage_required": 100.0,
     "description": "An Aurora borealis"},
    {"id": 22, "name": "aurora_borealis", "start": "2022-11-15T01:50:00+00:00",
     "end": "2022-11-15T03:50:46+00:00",
     "done": 'false', "max_points": 6000, "decrease_rate": 0.9,
     "zone": {"left": 16000, "right": 16600, "top": 9000, "bottom": 9400}, "optic_required": "NORMAL",
     "coverage_required": 80.0,
     "description": "Precise picture"},
    {"id": 23, "name": "aurora_borealis", "start": "2022-11-15T02:50:00+00:00",
     "end": "2022-11-15T05:35:46+00:00",
     "done": 'false', "max_points": 6000, "decrease_rate": 0.9,
     "zone": {"left": 4000, "right": 5000, "top": 3000, "bottom": 3700}, "optic_required": "NORMAL",
     "coverage_required": 78.0,
     "description": "An Aurora borealis is visible from space, can you ask MELVIN to take a picture of it for us please?"},
     #{"id": 4, "name": "aurora_borealis", "start": "2022-11-14T20:10:00+00:00",
     #"end": "2022-11-14T22:50:46+00:00",
     #"done": 'false', "max_points": 6000, "decrease_rate": 0.9,
     #"zone": {"left": 10000, "right": 11000, "top": 7000, "bottom": 9300}, "optic_required": "NORMAL",
     #"coverage_required": 100.0,
     #"description": "An Aurora borealis"},
    {"id": 25, "name": "aurora_borealis", "start": "2022-11-15T03:48:00+00:00",
     "end": "2022-11-15T04:50:46+00:00",
     "done": 'false', "max_points": 6000, "decrease_rate": 0.9,
     "zone": {"left": 3450, "right": 3950, "top": 7000, "bottom": 7400}, "optic_required": "NARROW",
     "coverage_required": 80.0,
     "description": "Precise picture"},
    {"id": 26, "name": "aurora_borealis", "start": "2022-11-15T05:51:00+00:00",
     "end": "2022-11-15T08:35:46+00:00",
     "done": 'false', "max_points": 6000, "decrease_rate": 0.9,
     "zone": {"left": 5000, "right": 6000, "top": 4000, "bottom": 5400}, "optic_required": "WIDE",
     "coverage_required": 100.0,
     "description": "An Aurora borealis is visible from space, can you ask MELVIN to take a picture of it for us please?"}
    ]

url = "http://192.168.5.2:11004/"
image_format = '.webp'


