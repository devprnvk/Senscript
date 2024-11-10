from pyspark.sql import SparkSession
from pyspark.sql.functions import to_date
from delta import configure_spark_with_delta_pip
import matplotlib.pyplot as plt
import seaborn as sns

builder = SparkSession.builder.appName("DeltaApp")
spark = configure_spark_with_delta_pip(builder) \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

data_df = spark.read.format("delta").load("Senscript/data/table")

data_df = data_df.withColumn("date", to_date(data_df["timestamp"]))

aggregated_df = data_df.groupBy("emotion").agg(
    {"typingSpeed": "avg", "syntaxErrors": "avg", "windowSwitchCount": "avg"}
)

aggregated_df.show()


pandas_df = aggregated_df.toPandas()

print(pandas_df.head())


sns.set(style="whitegrid")


plt.figure(figsize=(10, 6))

sns.barplot(x="emotion", y="avg(typingSpeed)", data=pandas_df)
plt.title("Average Typing Speed by Emotion")
plt.xlabel("Emotion")
plt.ylabel("Average Typing Speed")
plt.xticks(rotation=45)
plt.show()

plt.figure(figsize=(10, 6))
sns.barplot(x="emotion", y="avg(syntaxErrors)", data=pandas_df)
plt.title("Average Syntax Errors by Emotion")
plt.xlabel("Emotion")
plt.ylabel("Average Syntax Errors")
plt.xticks(rotation=45)
plt.show()

plt.figure(figsize=(10, 6))
sns.barplot(x="emotion", y="avg(windowSwitchCount)", data=pandas_df)
plt.title("Average Window Switches by Emotion")
plt.xlabel("Emotion")
plt.ylabel("Average Window Switches")
plt.xticks(rotation=45)
plt.show()
