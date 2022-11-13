import cv2
import imutils as imutils
import numpy as np

img1 = cv2.imread("edited.png")
img2 = cv2.imread("original.png")
diff = cv2.absdiff(img1, img2)
mask = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
th = 1
imask =  mask>th
canvas = np.zeros_like(img2, np.uint8)
canvas[imask] = img2[imask]


black = canvas[0,0,:].astype(int)
mask = cv2.inRange(canvas, black, black)

cv2.imwrite("a.png",mask)
img = cv2.imread('a.png')

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
#Black Color
lower_black = np.array([0,0,0])
upper_black = np.array([0,0,0])

black = cv2.inRange(hsv, lower_black, upper_black)

cnts = cv2.findContours(black,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)

for c in cnts:
    cv2.drawContours(img,[c],-1,(0,255,0),3)
    # compute the center of the contour
    M = cv2.moments(c)
    if M["m00"] != 0:
     cX = int(M["m10"] / M["m00"])
     cY = int(M["m01"] / M["m00"])
    else:
     cX, cY = 0, 0

    print(cX,cY)



