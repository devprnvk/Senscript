from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allows cross-origin requests from VS Code extension

# Store the latest emotion
current_emotion = {"mood": "neutral"}

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

@app.route('/current_emotion', methods=['GET'])
def get_current_emotion():
    return jsonify(current_emotion), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)