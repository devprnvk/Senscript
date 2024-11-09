import pyspark
from delta.tables import DeltaTable
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip

# Initialize Spark session with Delta support
builder = SparkSession.builder.appName("DeltaApp")

# Apply Delta configurations
spark = configure_spark_with_delta_pip(builder) \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

# Define the Delta table path
delta_path = "Senscript/data/synthetic_table"  # Replace with the actual path to your Delta table

# Read the Delta table
delta_table = DeltaTable.forPath(spark, delta_path)
delta_df = delta_table.toDF()

# Show the data from the Delta table
delta_df.show()