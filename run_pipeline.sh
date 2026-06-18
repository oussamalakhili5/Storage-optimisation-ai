#!/bin/bash

# ====================================================================
# Storage Optimization AI - Big Data Pipeline Orchestrator
# ====================================================================
# This script automates the complete data flow:
# 1. Generates new simulated storage data
# 2. Uploads the raw CSV to the Hadoop (HDFS) container
# 3. Triggers the PySpark pipeline to process, classify, and upsert
#    the data into MongoDB.
# ====================================================================

echo "=============================================="
echo " Starting Storage Optimization AI Pipeline"
echo "=============================================="

# Stop script on first error
set -e

# ---------------------------------------------------------
# Step 1: Generate the raw dataset
# ---------------------------------------------------------
echo ""
echo "[1/3] Generating new dataset..."
# Assuming generate_dataset.py writes to backend/app/data/storage_data.csv
python3 backend/generate_dataset.py

# ---------------------------------------------------------
# Step 2: Upload to HDFS
# ---------------------------------------------------------
echo ""
echo "[2/3] Uploading CSV to HDFS..."
# Copy the local file into the namenode container temporarily
docker cp backend/app/data/storage_data.csv namenode:/tmp/storage_data.csv

# Ensure the target directory exists in HDFS, then put the file
docker exec namenode hdfs dfs -mkdir -p /data/
docker exec namenode hdfs dfs -put -f /tmp/storage_data.csv /data/storage_data.csv

# ---------------------------------------------------------
# Step 3: Trigger Spark Job
# ---------------------------------------------------------
echo ""
echo "[3/3] Executing PySpark Big Data Job..."
# Assuming you mount your local ./backend directory to /opt/backend inside the spark-master container.
# Adjust the path '/opt/backend/spark_pipeline.py' depending on your docker-compose volumes!
docker exec spark-master spark-submit \
    --master spark://spark-master:7077 \
    --packages org.mongodb.spark:mongo-spark-connector_2.12:10.2.1 \
    /opt/backend/spark_pipeline.py

echo ""
echo "=============================================="
echo " Pipeline completed successfully!"
echo "=============================================="
