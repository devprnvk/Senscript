from flask import Flask, Response, jsonify, request, render_template_string
from flask_cors import CORS
from flask import send_from_directory

import cv2
import mediapipe as mp

app = Flask(__name__)
CORS(app)

import os

@app.route('/<filename>')
def serve_file(filename):
    return send_from_directory(os.getcwd(), filename)

# Store the latest emotion
current_emotion = {"mood": "neutral"}

# Initialize Mediapipe face mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Route for updating the current emotion
@app.route('/emotion', methods=['POST'])
def update_emotion():
    global current_emotion
    data = request.get_json()
    mood = data.get("mood")
    if mood:
        current_emotion["mood"] = mood
        print(f"Updated mood: {mood}")
        return jsonify({"status": "success", "message": "Emotion updated"}), 200
    return jsonify({"status": "error", "message": "Invalid data"}), 400

# Route to get the current emotion
@app.route('/current_emotion', methods=['GET'])
def get_current_emotion():
    return jsonify(current_emotion), 200

# Route to serve the video feed with face mesh overlays
def gen_frames():
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
        
        # Convert BGR image to RGB for processing with Mediapipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = mp_face_mesh.process(frame_rgb)

        # Draw the face mesh annotations on the frame
        if results.multi_face_landmarks:
            for landmark in results.multi_face_landmarks:
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=landmark,
                    connections=mp.solutions.face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style()
                )
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=landmark,
                    connections=mp.solutions.face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing.DrawingSpec(color=(256, 256, 256), thickness=2, circle_radius=1)
                )

        # Encode the frame as JPEG
        _, buffer = cv2.imencode('.jpg', cv2.flip(frame, 1))
        frame_data = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n\r\n')

    cap.release()

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def video_page():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SentiCode</title>
        <style>
            @font-face {
                font-family: "Work Sans";
                src: url("WorkSans-VariableFont_wght.ttf") format("woff");
                font-weight: 100 900;
                font-style: normal;
            }

            body {
                font-family: "Work Sans", serif;
                font-weight: 400;
                font-style: normal;
                background: linear-gradient(to bottom, #120c4a, #0d278f);
                color: #333;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                min-height: 100vh;
            }

            .container {
                text-align: center;
                padding: 80px 20px;
                max-width: 600px;
                margin: auto;
            }

            h1 {
                margin-bottom: 40px;
                color: white;
            }

            .video-container {
                border: 5px solid #ffffff;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 4px 8px rgba(199, 199, 199, 0.3);
                background-color: rgba(255, 255, 255, 0.3);
                padding: 10px;
            }

            img {
                display: block;
                width: 100%;
                height: auto;
                max-width: 640px;
                border-radius: 10px;
            }

            /* New style for the emotion box */
            .emotion-box {
                display: inline-block;
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 25px;
                padding: 10px 20px;
                font-size: 20px;
                font-weight: bold;
                color: #333;
                margin-top: 20px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }

            /* Styling the footer */
            .footer {
                margin-top: auto;
                padding: 20px;
                text-align: center;
                font-size: 14px;
                color: white;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>SentiCode Emotional Wellness Detection</h1>
            <div class="video-container">
                <img src="/video_feed" alt="Facial Landmark Video Feed">
            </div>
            <!-- Emotion display box -->
            <div id="emotion-box" class="emotion-box">Emotion: neutral</div>
            <div class="footer">
                © 2024 Facial Detection Demo
            </div>
        </div>

        <script>
            // Function to fetch and update the current emotion
            function updateEmotion() {
                fetch('/current_emotion')
                    .then(response => response.json())
                    .then(data => {
                        const emotionBox = document.getElementById('emotion-box');
                        emotionBox.textContent = 'Emotion: ' + data.mood;
                    })
                    .catch(error => console.error('Error fetching emotion:', error));
            }

            // Update the emotion every 2 seconds
            setInterval(updateEmotion, 2000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
