import os, cv2
import numpy as np
import sys

#Python script used by the crontab to stitch the global map every 10 minutes
#Documentation available at stitching.py

try:
    offset = [int(sys.argv[3]),int(sys.argv[4])] #offset[0] = y, offset[1] = x
    ho,wo = int(sys.argv[1]),int(sys.argv[2]) #set height and width of final saved image
    h,w = 10800, 21600
    out = np.zeros((h*2,w*2,3), np.uint8)
    path = sys.argv[5] + '/'
    mylist = os.listdir(path)
except:
    print('invalid arguments, correct syntax is: [height] [width] [yoffset] [xoffset] [path]')
    sys.exit()

print(str(offset[0]) + ' ' + str(offset[1]))

def parse(fname):
    step = fname.split('|')
    print(step)
    last = step[4].split('.')
    coords = [step[3],last[0]]
    return coords

for fname in mylist:
    if 'outs' in fname or 'stitcher' in fname:
        continue
    coords = parse(fname)
    tmp = cv2.imread(path + fname)
    print('Image @ ' + coords[1] + ':' + coords[0] + '... ')
    y,x= int(int(coords[1])+(h/2)), int(int(coords[0])+(w/2))
    out[y: y + 600, x: x + 600 ] = tmp
    
    if x-w/2 + 600 > w:
        out[y: y + 600, x - w: x + 600 - w ] = tmp
    if x-w/2 - 600 < 0:
        out[y: y + 600, x + w: x + 600 + w ] = tmp
    if y-h/2 + 600 > h:
        out[y - h: y + 600 - h, x: x + 600 ] = tmp
    if y-h/2 - 600 < 0:
        out[y + h: y + 600 + h, x: x + 600 ] = tmp
        
print('Saving...')
cv2.imwrite('/home/user/melvin_unknown/map/outs.png',out[int(h/2+300) + offset[0] : int(h/2+300) + offset[0] + ho, int(w/2+300) + offset[1] : int(w/2+300) + wo + offset[1]])
