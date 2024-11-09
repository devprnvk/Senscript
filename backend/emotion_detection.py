import cv2
from deepface import DeepFace
import requests
import time

# URL for posting emotion to the Flask backend
SERVER_URL = "http://localhost:8080/emotion"

def detect_emotion(frame):
    try:
        # Analyze the frame with DeepFace and extract the dominant emotion
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        emotion = result['dominant_emotion']
        return emotion
    except Exception as e:
        print(f"Error detecting emotion: {e}")
        return None

def send_emotion_to_server(emotion):
    try:
        # Send the detected emotion to the Flask backend
        response = requests.post(SERVER_URL, json={'mood': emotion})
        if response.status_code == 200:
            print(f"Emotion '{emotion}' sent successfully.")
        else:
            print("Failed to send emotion to server.")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")

def main():
    # Initialize the webcam (change to 1 or another index if you have multiple cameras)
    cap = cv2.VideoCapture(0)

    # Check if the webcam opened successfully
    if not cap.isOpened():
        print("Error: Could not open video capture.")
        return

    # Continuously capture frames and analyze emotions
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            break

        # Resize the frame for faster processing if needed
        frame = cv2.resize(frame, (640, 480))

        # Detect emotion
        emotion = detect_emotion(frame)

        # If an emotion was detected, send it to the server
        if emotion:
            send_emotion_to_server(emotion)

        # Wait a bit before capturing the next frame to prevent excessive load
        time.sleep(2)

    # Release the capture when done
    cap.release()

if __name__ == "__main__":
    main()