import cv2

cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    print("Webcam access successful!")
cap.release()