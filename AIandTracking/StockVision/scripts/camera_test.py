import cv2

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # force DirectShow
cam2 = cv2.VideoCapture(1, cv2.CAP_DSHOW) 
print("Opened:", cam.isOpened())
print("Opened:", cam2.isOpened())

