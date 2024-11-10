# [Main Server for the program]
# Import Libraries

import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Lock

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from delta.tables import *
from delta import configure_spark_with_delta_pip

builder = SparkSession.builder.appName("DeltaApp")

# Spark Configuration

spark = configure_spark_with_delta_pip(builder) \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

print(spark.version)

# Main Schema for Data Categorization

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

# Flask App 

app = Flask(__name__)
CORS(app)
current_emotion = {"mood": "neutral"}
emotion_lock = Lock()
log_data = []

# API for the emotion updates

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

# Get the Current Emotion

@app.route('/current_emotion', methods=['GET'])
def get_current_emotion():
    with emotion_lock:
        return jsonify(current_emotion), 200

# Log the Emotion Data

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

# Get the Log Data 

@app.route('/log_data', methods=['GET'])
def get_log_data():
    delta_table = DeltaTable.forPath(spark, delta_path)
    log_df = delta_table.toDF()
    log_data_json = log_df.toJSON().collect()
    return jsonify(log_data_json), 200

# Host for application

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)