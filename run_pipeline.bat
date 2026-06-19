@echo off
echo ==============================================
echo  Starting Storage Optimization AI Pipeline
echo ==============================================

:: 1. Generate the raw dataset
echo.
echo [1/3] Generating new dataset...
python backend\generate_dataset.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Dataset generation failed.
    exit /b %ERRORLEVEL%
)

:: 2. Upload to HDFS
echo.
echo [2/3] Uploading CSV to HDFS...
docker cp backend\app\data\storage_data.csv hadoop_namenode:/tmp/storage_data.csv
docker exec hadoop_namenode hdfs dfs -mkdir -p /data/
docker exec hadoop_namenode hdfs dfs -put -f /tmp/storage_data.csv /data/storage_data.csv
if %ERRORLEVEL% neq 0 (
    echo [ERROR] HDFS upload failed.
    exit /b %ERRORLEVEL%
)

:: 3. Trigger Spark Job
echo.
echo [3/3] Executing PySpark Big Data Job...
:: We must copy the script into the spark container first, since there are no volumes mounted for it
docker cp backend\spark_pipeline.py spark_master:/tmp/spark_pipeline.py
docker exec spark_master spark-submit --master spark://spark-master:7077 --packages org.mongodb.spark:mongo-spark-connector_2.12:10.2.1 /tmp/spark_pipeline.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Spark Job failed.
    exit /b %ERRORLEVEL%
)

echo.
echo ==============================================
echo  Pipeline completed successfully!
echo ==============================================
