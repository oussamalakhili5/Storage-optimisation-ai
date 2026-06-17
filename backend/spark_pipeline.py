"""
Spark Big Data Processing Pipeline

Reads raw storage metrics from HDFS (CSV), applies business-rule classification,
and writes the enriched DataFrame into MongoDB (collection: server_metrics).

Business Rules — server_status:
    - 'Normal'   : utilization < 50%
    - 'Chargé'   : 50% <= utilization <= 80%
    - 'Critique'  : utilization > 80%

Usage (submit to Spark cluster):
    spark-submit --master spark://spark-master:7077 \
        --packages org.mongodb.spark:mongo-spark-connector_2.12:10.2.1 \
        spark_pipeline.py
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, round as spark_round, when


# ============================================
# 1. Initialize Spark Session
# ============================================

SPARK_MASTER = "spark://spark-master:7077"
MONGO_OUTPUT_URI = "mongodb://admin:admin123@mongodb:27017/storage_db.server_metrics"
HDFS_CSV_PATH = "hdfs://namenode:9000/data/storage_data.csv"

spark = (
    SparkSession.builder
    .appName("StorageOptimization-Pipeline")
    .master(SPARK_MASTER)
    # ---- MongoDB Spark Connector configuration ----
    .config("spark.mongodb.output.uri", MONGO_OUTPUT_URI)
    .config(
        "spark.jars.packages",
        "org.mongodb.spark:mongo-spark-connector_2.12:10.2.1",
    )
    .getOrCreate()
)

print("=" * 60)
print("  Spark session initialized")
print(f"  Master : {SPARK_MASTER}")
print(f"  AppName: {spark.sparkContext.appName}")
print("=" * 60)


# ============================================
# 2. Read raw CSV from HDFS
# ============================================

print(f"\n[STEP 1] Reading CSV from HDFS: {HDFS_CSV_PATH}")

df_raw = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv(HDFS_CSV_PATH)
)

print(f"  → {df_raw.count()} rows loaded")
print(f"  → Schema:")
df_raw.printSchema()


# ============================================
# 3. Compute utilization_percent
# ============================================

print("[STEP 2] Computing utilization_percent column ...")

df_with_util = df_raw.withColumn(
    "utilization_percent",
    spark_round(
        (col("used_storage") / col("total_storage")) * 100,
        2,
    ),
)


# ============================================
# 4. Apply business rules → server_status
# ============================================

print("[STEP 3] Classifying servers by utilization ...")

df_classified = df_with_util.withColumn(
    "server_status",
    when(col("utilization_percent") < 50, "Normal")
    .when(col("utilization_percent") <= 80, "Chargé")
    .otherwise("Critique"),
)

# Preview the result
print("\n  → Classified DataFrame sample:")
df_classified.show(truncate=False)

# Quick summary per status
print("  → Distribution by server_status:")
df_classified.groupBy("server_status").count().show()


# ============================================
# 5. Write to MongoDB (append mode)
# ============================================

print("[STEP 4] Writing classified data to MongoDB ...")
print(f"  → Target: {MONGO_OUTPUT_URI}")

(
    df_classified.write
    .format("mongodb")
    .mode("append")
    .option("uri", MONGO_OUTPUT_URI)
    .save()
)

rows_written = df_classified.count()
print(f"  → {rows_written} documents written to MongoDB successfully")


# ============================================
# 6. Cleanup
# ============================================

print("\n" + "=" * 60)
print("  Pipeline finished successfully")
print("=" * 60)

spark.stop()
