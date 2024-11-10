import random
import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from delta import configure_spark_with_delta_pip

builder = SparkSession.builder.appName("DeltaApp")
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

emotions = ["neutral", "happy", "angry", "sad", "fear"]

delta_path = "Senscript/data/table"

def generate_synthetic_data(num_records):
    data = []
    for _ in range(num_records):
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
            typing_speed = random.randint(30, 40)
            syntax_errors = random.randint(2, 4)
            window_switch_count = random.randint(4, 8)
        elif emotion == "fear":
            typing_speed = random.randint(25, 35)
            syntax_errors = random.randint(1, 4)
            window_switch_count = random.randint(3, 7)

        received_at = datetime.datetime.now().isoformat()
        timestamp = datetime.datetime.now().isoformat()
        
        data.append((emotion, typing_speed, syntax_errors, window_switch_count, received_at, timestamp))
    
    return data

synthetic_data = generate_synthetic_data(100)
synthetic_df = spark.createDataFrame(synthetic_data, schema)
synthetic_df.write.format("delta").mode("append").save(delta_path)