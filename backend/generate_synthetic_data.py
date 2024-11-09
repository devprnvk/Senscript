import random
import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from delta import configure_spark_with_delta_pip

# Initialize Spark session with Delta support
builder = SparkSession.builder.appName("DeltaApp")
spark = configure_spark_with_delta_pip(builder) \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

# Define the schema for the log data
schema = StructType([
    StructField("emotion", StringType(), True),
    StructField("typingSpeed", IntegerType(), True),
    StructField("syntaxErrors", IntegerType(), True),
    StructField("windowSwitchCount", IntegerType(), True),
    StructField("received_at", StringType(), True),
    StructField("timestamp", StringType(), True)
])

# List of emotions to simulate
emotions = ["neutral", "happy", "angry", "sad", "fear"]

# Path to your Delta table
delta_path = "Senscript/data/synthetic_table"

# Function to generate synthetic data with realistic patterns
def generate_synthetic_data(num_records):
    data = []
    for _ in range(num_records):
        # Select an emotion and adjust other values based on it
        emotion = random.choices(
            ["neutral", "happy", "angry", "sad", "fear"], 
            weights=[0.4, 0.2, 0.15, 0.15, 0.1]
        )[0]

        if emotion == "happy":
            typing_speed = random.randint(60, 80)
            syntax_errors = random.randint(0, 1)
            window_switch_count = random.randint(0, 2)
        elif emotion == "neutral":
            typing_speed = random.randint(50, 70)
            syntax_errors = random.randint(0, 3)
            window_switch_count = random.randint(0, 4)
        elif emotion == "angry":
            typing_speed = random.randint(20, 50)
            syntax_errors = random.randint(3, 5)
            window_switch_count = random.randint(5, 10)
        elif emotion == "sad":
            typing_speed = random.randint(30, 60)
            syntax_errors = random.randint(2, 4)
            window_switch_count = random.randint(4, 8)
        elif emotion == "fear":
            typing_speed = random.randint(25, 55)
            syntax_errors = random.randint(1, 4)
            window_switch_count = random.randint(3, 7)

        # Current timestamp for both 'received_at' and 'timestamp'
        received_at = datetime.datetime.now().isoformat()
        timestamp = datetime.datetime.now().isoformat()
        
        # Append a record to the list
        data.append((emotion, typing_speed, syntax_errors, window_switch_count, received_at, timestamp))
    
    return data

# Generate 1000 records of synthetic data
synthetic_data = generate_synthetic_data(1000)

# Convert the list to a Spark DataFrame
synthetic_df = spark.createDataFrame(synthetic_data, schema)

# Append the data to the Delta Lake table
synthetic_df.write.format("delta").mode("append").save(delta_path)