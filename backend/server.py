import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Lock

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

# Verify Delta support
print(spark.version)  # Check if Spark session is created successfully

# Define the schema for the log data (without the duration field)
schema = StructType([
    StructField("emotion", StringType(), True),
    StructField("typingSpeed", IntegerType(), True),
    StructField("syntaxErrors", IntegerType(), True),
    StructField("windowSwitchCount", IntegerType(), True),
    StructField("received_at", StringType(), True),
    StructField("timestamp", StringType(), True)
])

# Path to your Delta Lake table (you can replace this with a local directory or cloud path)
delta_path = "Senscript/data/table"  # Set the actual path here

# Create Delta table if it doesn't exist
if not DeltaTable.isDeltaTable(spark, delta_path):
    # Create an empty DataFrame with the schema
    spark.createDataFrame([], schema).write.format("delta").save(delta_path)

# Flask app setup
app = Flask(__name__)
CORS(app)  # Allows cross-origin requests from VS Code extension

# Store the latest emotion with thread safety
current_emotion = {"mood": "neutral"}
emotion_lock = Lock()

# Initialize log_data as an empty list to store log entries (optional, not needed now for Delta)
log_data = []

@app.route('/emotion', methods=['POST'])
def update_emotion():
    data = request.get_json()
    mood = data.get("mood")

    if mood:
        with emotion_lock:  # Lock for thread safety
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

    # Remove the 'duration' field if it exists
    if 'duration' in data:
        del data['duration']

    # Check if all necessary data is received
    required_fields = ["emotion", "typingSpeed", "syntaxErrors", "windowSwitchCount"]
    if all(field in data for field in required_fields):
        # Add the timestamp for when data was received
        data['received_at'] = datetime.datetime.now().isoformat()
        data['timestamp'] = datetime.datetime.now().isoformat()

        # Create a Spark DataFrame for the new entry
        log_df = spark.createDataFrame([data], schema)

        # Write the new entry to Delta, partitioned by emotion
        log_df.write.format("delta").partitionBy("emotion").mode("append").save(delta_path)

        # Perform the merge operation to ensure the data is added correctly
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
# New route to retrieve log data via GET
@app.route('/log_data', methods=['GET'])
def get_log_data():
    # Read the data from the Delta Lake table
    delta_table = DeltaTable.forPath(spark, delta_path)
    log_df = delta_table.toDF()

    # Convert the DataFrame to JSON
    log_data_json = log_df.toJSON().collect()
    
    # Return the logged data as JSON
    return jsonify(log_data_json), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)