import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Lock

from flask import Flask, Response, jsonify, request, render_template_string
from flask_cors import CORS
from flask import send_from_directory

import cv2
import mediapipe as mp

# Delta Lake Imports
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from delta.tables import *
from delta import configure_spark_with_delta_pip

# Initialize Spark session with Delta support using configure_spark_with_delta_pip
builder = SparkSession.builder.appName("DeltaApp")

# Apply Delta configurations
spark = configure_spark_with_delta_pip(builder) \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()


schema = StructType([
    StructField("emotion", StringType(), True),
    StructField("typingSpeed", IntegerType(), True),
    StructField("syntaxErrors", IntegerType(), True),
    StructField("windowSwitchCount", IntegerType(), True),
    StructField("received_at", StringType(), True),
    StructField("timestamp", StringType(), True)
])


delta_path = "Senscript/data/table"


if not DeltaTable.isDeltaTable(spark, delta_path):
    spark.createDataFrame([], schema).write.format("delta").save(delta_path)


app = Flask(__name__)
CORS(app)

import os

@app.route('/<filename>')
def serve_file(filename):
    return send_from_directory(os.getcwd(), filename)


current_emotion = {"mood": "neutral"}
emotion_lock = Lock()

log_data = []

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

@app.route('/emotion', methods=['POST'])
def update_emotion():
    data = request.get_json()
    mood = data.get("mood")

    if mood:
        with emotion_lock:
            current_emotion["mood"] = mood
        print(f"Updated mood: {mood}")
        return jsonify({"status": "success", "message": "Emotion updated"}), 200
    
    return jsonify({"status": "error", "message": "Invalid data"}), 400


@app.route('/current_emotion', methods=['GET'])
def get_current_emotion():
    with emotion_lock:
        return jsonify(current_emotion), 200

@app.route('/log', methods=['POST'])
def log_emotion_data():
    data = request.json

    if 'duration' in data:
        del data['duration']

    required_fields = ["emotion", "typingSpeed", "syntaxErrors", "windowSwitchCount"]
    if all(field in data for field in required_fields):
        data['received_at'] = datetime.datetime.now().isoformat()
        data['timestamp'] = datetime.datetime.now().isoformat()

        log_df = spark.createDataFrame([data], schema)

        log_df.write.format("delta").partitionBy("emotion").mode("append").save(delta_path)

        delta_table = DeltaTable.forPath(spark, delta_path)
        delta_table.alias("t").merge(
            log_df.alias("s"),
            "t.timestamp = s.timestamp")\
            .whenNotMatchedInsert(values={
                "emotion": "s.emotion",
                "typingSpeed": "s.typingSpeed",
                "syntaxErrors": "s.syntaxErrors",
                "windowSwitchCount": "s.windowSwitchCount",
                "received_at": "s.received_at",
                "timestamp": "s.timestamp"
            }).execute()

        print("Logged data:", data)
        return jsonify({"status": "success", "data": data}), 200
    else:
        return jsonify({"status": "error", "message": "Missing required data"}), 400
@app.route('/log_data', methods=['GET'])
def get_log_data():
    delta_table = DeltaTable.forPath(spark, delta_path)
    log_df = delta_table.toDF()

    log_data_json = log_df.toJSON().collect()
    
    return jsonify(log_data_json), 200

def gen_frames():
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = mp_face_mesh.process(frame_rgb)

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
