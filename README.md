# Storage Optimization AI

> A Big Data and AI platform for proactive storage monitoring, predictive capacity planning, and server saturation risk analysis.

## Executive Summary

Managing storage capacity in large-scale data centers requires proactive, not reactive, decision-making. **Storage Optimization AI** implements a full end-to-end Big Data pipeline designed to ingest, process, analyze, and forecast server storage metrics.

By applying Machine Learning to historical utilization data, the system predicts capacity exhaustion before it becomes operationally critical. This helps infrastructure teams scale resources at the right time, reducing costly over-provisioning while avoiding downtime caused by saturated storage nodes.

The project supports two main development paths:

- **Local Demo Mode:** Runs the frontend and a standalone FastAPI server using local CSV data and JSON authentication for fast prototyping.
- **Big Data Mode:** Runs the full production-style ecosystem with MongoDB, Hadoop HDFS, Apache Spark, and the production FastAPI backend through Docker Compose.

## Architecture Overview

This ecosystem follows a modern batch-processing architecture, similar to a Lambda architecture without the speed layer. It emphasizes data decoupling, reproducible processing, fault tolerance, and a clear separation between ingestion, processing, serving, and visualization.

```text
[Raw Telemetry / CSV]
        |
        v
[Hadoop HDFS - Cold Storage]
        |
        v
[Apache Spark - PySpark Cluster] -----> [Scikit-Learn Model Training]
        |                                         |
        v                                         v
[MongoDB - Idempotent Serving] <---------- [storage_model.pkl]
        |
        v
[FastAPI Secured Backend]
        |
        v
[React + Vite Dashboard - Recharts]
```

| Layer | Role |
| --- | --- |
| **Data Lake - HDFS** | Stores raw server telemetry in Hadoop Distributed File System as the cold-storage foundation. |
| **Processing Engine - Apache Spark** | Reads raw CSV telemetry, computes utilization metrics, applies business rules, and prepares data for serving. |
| **Serving Layer - MongoDB** | Stores processed server metrics and user records in a document database for API consumption. |
| **Machine Learning - Scikit-Learn** | Trains per-server Linear Regression models to forecast future storage usage. |
| **API and UI - FastAPI + React** | Exposes metrics, alerts, forecasts, and authentication flows to an interactive dashboard. |

## Key Features

- **Idempotent Data Processing:** The Spark-to-MongoDB pipeline uses an upsert strategy based on `server_id` and `date`, preventing duplicate records during retries or repeated batch runs.
- **AI-Driven Capacity Forecasting:** Scikit-Learn models forecast future storage usage per server, helping teams identify saturation risk before it becomes critical.
- **Interactive Telemetry Dashboard:** The React dashboard visualizes historical storage usage, alerts, recommendations, statistics, anomalies, and forecast outputs.
- **Automated Orchestration:** Batch scripts support local startup and pipeline execution, making the workflow easier to run manually or schedule with Cron or Windows Task Scheduler.
- **Secured Backend APIs:** JWT-based authentication protects the main storage, alert, and forecasting endpoints.
- **Dual Operating Modes:** The project can run as a lightweight local demo or as a full containerized Big Data environment.

## Technical Stack

| Layer | Technologies |
| --- | --- |
| **Frontend** | React, Vite, Recharts, CSS |
| **Backend** | Python 3.10+, FastAPI, Uvicorn, Pydantic, Marshmallow |
| **Authentication** | JWT, bcrypt, passlib, PyJWT |
| **Database** | MongoDB, PyMongo |
| **Big Data Storage** | Hadoop HDFS |
| **Big Data Processing** | Apache Spark, PySpark, MongoDB Spark Connector |
| **Machine Learning** | Scikit-Learn, Pandas, NumPy, Pickle |
| **Infrastructure** | Docker, Docker Compose, Bash scripts, Windows batch scripts |

## Project Structure

```text
storage-optimization-ai/
|-- README.md
|-- .env.example
|-- docker-compose.yml
|-- run_pipeline.sh
|-- run_pipeline.bat
|-- start_project.bat
|-- backend/
|   |-- main.py                         # Production FastAPI backend
|   |-- dev_server.py                   # Standalone local demo backend
|   |-- spark_pipeline.py               # PySpark HDFS-to-MongoDB pipeline
|   |-- requirements.txt
|   |-- users_db.json                   # Local demo auth storage
|   |-- app/
|   |   |-- database.py                 # MongoDB connections and indexes
|   |   |-- data/
|   |   |   |-- storage_data.csv         # Sample storage telemetry
|   |   |   `-- storage_model.pkl        # Trained forecast model artifact
|   |   |-- modules/
|   |   |   |-- prediction.py            # ML training and forecast logic
|   |   |   |-- anomaly_detection.py     # Outlier detection logic
|   |   |   |-- alerts.py
|   |   |   |-- recommendations.py
|   |   |   `-- storage_analysis.py
|   |   `-- routes/
|   |       |-- auth_routes.py
|   |       |-- storage_routes.py
|   |       |-- alert_routes.py
|   |       |-- prediction_routes.py
|   |       `-- report_routes.py
|   |-- auth/
|   |   |-- jwt_manager.py
|   |   `-- decorators.py
|   |-- schemas/
|   `-- utils/
|-- frontend/
|   |-- package.json
|   |-- vite.config.js
|   |-- index.html
|   `-- src/
|       |-- App.jsx
|       |-- main.jsx
|       |-- components/
|       `-- pages/
|-- notebooks/
|   `-- model_training.ipynb
`-- docs/
    |-- cahier_de_charge.pdf
    `-- rapport_final.docx
```

## Getting Started

### Prerequisites

Install the following tools before running the project:

- Git
- Python 3.10+
- Node.js 18+ and npm
- Docker Desktop with Docker Compose

Docker is only required for the full Big Data mode.

## Path A: Quick Start - Local Demo Mode

Local Demo Mode runs the dashboard without Docker, MongoDB, Hadoop, or Spark. It reads from local CSV data and uses a local JSON file for authentication.

### Automated Launcher - Windows

From the project root:

```powershell
.\start_project.bat
```

The script starts:

| Service | URL |
| --- | --- |
| Backend API | `http://127.0.0.1:8000` |
| Backend Docs | `http://127.0.0.1:8000/docs` |
| Frontend UI | `http://localhost:5173` |

### Manual Setup

Start the backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn dev_server:app --reload --port 8000
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

Start the frontend in a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the application:

```text
http://localhost:5173
```

## Path B: Full Scale - Docker and Big Data Mode

Big Data Mode starts the full containerized infrastructure: backend, MongoDB, Hadoop HDFS, Spark master, and Spark worker.

### Environment Initialization

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Ensure the root `.env` file defines the MongoDB database name required by `docker-compose.yml`:

```env
MONGO_DB=storage_db
```

The Spark pipeline currently reads:

```text
hdfs://namenode:9000/data/storage_data.csv
```

Keep your HDFS path aligned with:

```env
HDFS_FILE_PATH=/data/storage_data.csv
```

### Launch Infrastructure

```bash
docker compose up -d --build
```

If your Docker installation uses the legacy command:

```bash
docker-compose up -d --build
```

### Useful Infrastructure Endpoints

| Service | URL |
| --- | --- |
| Backend API Docs | `http://localhost:8000/docs` |
| Hadoop NameNode UI | `http://localhost:9870` |
| Spark Master UI | `http://localhost:8080` |
| MongoDB Instance | `mongodb://localhost:27017` |

### Launch Frontend

```bash
cd frontend
npm install
npm run dev
```

## Data Pipeline and ML Workflow

Use the following workflow to feed raw server telemetry through the Big Data cluster and into the forecasting pipeline.

### 1. Ship Telemetry to HDFS

```bash
docker cp backend/app/data/storage_data.csv hadoop_namenode:/tmp/storage_data.csv
docker exec hadoop_namenode hdfs dfs -mkdir -p /data
docker exec hadoop_namenode hdfs dfs -put -f /tmp/storage_data.csv /data/storage_data.csv
```

### 2. Execute Spark Pipeline

```bash
docker cp backend/spark_pipeline.py spark_master:/tmp/spark_pipeline.py
docker exec spark_master spark-submit --master spark://spark-master:7077 --packages org.mongodb.spark:mongo-spark-connector_2.12:10.2.1 /tmp/spark_pipeline.py
```

The Spark job:

1. Reads the CSV from HDFS.
2. Computes `utilization_percent`.
3. Assigns `server_status` using business rules.
4. Writes the processed records into MongoDB.

### 3. Train Forecasting Models

After MongoDB contains historical telemetry, authenticate through the API and send a secured request:

```text
POST /api/storage/train
```

The backend trains one model per server and writes the forecast artifact to:

```text
backend/app/data/storage_model.pkl
```

## API Overview

Interactive API documentation is available at:

```text
http://localhost:8000/docs
```

### Core Public and Authentication Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/register/` | Register a new system engineer profile |
| `POST` | `/api/login/` | Authenticate a user and generate Bearer JWT tokens |
| `POST` | `/api/refresh/` | Renew short-lived access credentials |
| `GET` | `/api/me/` | Return the current authenticated user profile |

### Main Metrics and AI Analytics

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/storage/metrics` | Fetch latest metrics for all cluster nodes |
| `GET` | `/api/storage/history/{server_id}` | Retrieve historical time-series logs for a specific node |
| `POST` | `/api/storage/train` | Retrain Scikit-Learn forecasting models from MongoDB history |
| `GET` | `/api/storage/forecast/{server_id}` | Compute multi-day capacity projections for a server |
| `GET` | `/api/alerts/critical` | List servers violating critical saturation thresholds |

### Local Demo Endpoints

The local demo backend also exposes frontend-friendly endpoints without requiring MongoDB:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/storage/status` | Latest storage status |
| `GET` | `/storage/history` | Historical storage records |
| `GET` | `/storage/prediction` | Next-day storage predictions |
| `GET` | `/storage/anomalies` | Detected anomalies |
| `GET` | `/storage/alerts` | Storage alerts |
| `GET` | `/storage/recommendations` | Optimization recommendations |
| `GET` | `/storage/statistics` | Dashboard summary statistics |
| `GET` | `/storage/report` | Generated report summary |

## Troubleshooting

### `vite` is not recognized

Cause: frontend dependencies are missing or installation failed.

Fix:

```bash
cd frontend
npm install
npm run dev
```

### Forecast endpoint reports that the ML model is missing

Cause: `storage_model.pkl` has not been generated yet.

Fix:

1. Ensure MongoDB contains historical telemetry.
2. Log in to generate an access token.
3. Call `POST /api/storage/train`.
4. Retry the forecast endpoint.

### PySpark cannot establish an HDFS connection

Cause: Hadoop may still be starting, or the HDFS file path does not match the pipeline path.

Fix:

1. Confirm the Hadoop NameNode container is running.
2. Verify that the CSV exists in HDFS.
3. Confirm the pipeline path points to `/data/storage_data.csv`.

```bash
docker exec hadoop_namenode hdfs dfs -ls /data
```

### MongoDB connection fails

Cause: MongoDB is not running or `MONGO_DB` / `MONGO_URI` is misconfigured.

Fix:

```bash
docker compose ps
```

Expected backend container URI:

```env
MONGO_URI=mongodb://mongodb:27017/storage_db
```

## Future Improvements

- Add a unified cross-platform pipeline runner.
- Add automated backend tests for authentication, storage metrics, alerts, and forecasts.
- Add CI checks for frontend builds and backend smoke tests.
- Add model versioning for trained forecasting artifacts.
- Replace Linear Regression with stronger time-series models for seasonality-aware forecasting.
- Add role-based access control for infrastructure teams and administrators.
- Add deployment documentation for cloud or on-premise environments.

## Disclaimer

Storage Optimization AI is an educational and research-oriented system for demonstrating data engineering, infrastructure analytics, and applied Machine Learning. Forecasts and recommendations should be reviewed by qualified engineers before being used for production capacity decisions.
