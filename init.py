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

sched = BlockingScheduler()

data = [
        {"id": 4, "name": "aurora_borealis", "start": "2022-11-08T01:35:00+00:00",
         "end": "2022-11-08T02:59:46+00:00",
         "done": False, "max_points": 6000, "decrease_rate": 0.9,
         "zone": {"left": 12000, "right": 12850, "top": 8000, "bottom": 8900}, "optic_required": "NORMAL",
         "coverage_required": 100.0,
         "description": "An Aurora borealis is visible from space, can you ask MELVIN to take a picture of it for us please?"},
        {"id": 5, "name": "sick_luke", "start": "2022-11-07T01:37:00+00:00",
         "end": "2022-11-08T02:58:46+00:00",
         "done": False, "max_points": 6000, "decrease_rate": 0.9,
         "zone": {"left": 8000, "right": 8300, "top": 8000, "bottom": 8400}, "optic_required": "NARROW",
         "coverage_required": 90.0,
         "description": "SKERE"}
    ]

url = "http://192.168.5.2:11004/"
image_format = '.webp'