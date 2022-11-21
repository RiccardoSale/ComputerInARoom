from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime , timedelta
import base64
import json
import math
import os
import time
import cv2
import numpy as np
import requests
import json
import lzma

global active_objectives #Active objectives list
global taken  #Nume of images taken by job named photo
global vel_route
global real_vx #Actual x speed
global real_vy #Actual y speed
global t_photo
global scanx
global data
global cd
global block
global url
global cur_dir
global y_scan
global x_start
global y_center
global past_objective
global wide_scanx
global first_time
global past_unknown


x_start = 0
y_center = 0
wide_scanx = 0
scanx = 0
taken = 0
cd = ''
first_time = True
block = False

y_scan = {i: [] for i in range(10800)}
past_unknown = []
data = []
active_objectives = []
vel_route = []
past_objective = set()
cur_dir = os.getcwd()

sched = BlockingScheduler()
url = "http://192.168.5.2:11004/"
image_format = '.webp'




