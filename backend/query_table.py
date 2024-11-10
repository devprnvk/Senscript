# [Query Delta Table Code]
# Import libraries 

import pyspark
from delta.tables import DeltaTable
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip

builder = SparkSession.builder.appName("DeltaApp")

# Spark Configuration 

spark = configure_spark_with_delta_pip(builder) \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

# Synthetic Delta Table 

delta_path = "Senscript/data/synthetic_table"
delta_table = DeltaTable.forPath(spark, delta_path)
delta_df = delta_table.toDF()
delta_df.show()