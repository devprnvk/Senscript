# [Emotion-Detection Python Tool]

# Library Imports

import cv2
from deepface import DeepFace
import requests
import time

SERVER_URL = "http://localhost:8080/emotion"

# Detect the emotion found in the image 

def detect_emotion(frame):
    try:
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        emotion = result['dominant_emotion']
        return emotion
    except Exception as e:
        print(f"Error detecting emotion: {e}")
        return None

# Send the emotion found towards the server 

def send_emotion_to_server(emotion):
    try:
        response = requests.post(SERVER_URL, json={'mood': emotion})
        if response.status_code == 200:
            print(f"Emotion '{emotion}' sent successfully.")
        else:
            print("Failed to send emotion to server.")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")

# Starting point of the program

def main():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open video capture.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            break

        frame = cv2.resize(frame, (640, 480))

        emotion = detect_emotion(frame)

        if emotion:
            send_emotion_to_server(emotion)

        time.sleep(2)

    cap.release()

if __name__ == "__main__":
    main()