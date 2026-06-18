# 💾 Storage Optimization AI

<div align="center">
  <!-- <img src="docs/logo.png" alt="Project Logo" width="200"/> -->
  <p><strong>A Big Data & AI ecosystem for predictive data center maintenance and capacity planning.</strong></p>
</div>

---

## 📌 Executive Summary
Managing storage capacity in large-scale data centers requires proactive, not reactive, decision-making. The **Storage Optimization AI** project implements a full end-to-end Big Data pipeline designed to ingest, process, and forecast server storage metrics. By leveraging Machine Learning against historical utilization data, the system predicts capacity exhaustion, allowing infrastructure teams to scale resources exactly when needed, eliminating both costly over-provisioning and critical downtime.

## 🏗️ Architecture Overview
This ecosystem follows a modern batch processing architecture (Lambda without the speed layer) ensuring robust data decoupling and fault tolerance:

1. **Data Lake (HDFS):** Raw server telemetry is ingested and immutably stored in a Hadoop Distributed File System, acting as the cold storage foundation.
2. **Processing Engine (Apache Spark):** PySpark clusters read the raw data, compute utilization heuristics, apply threshold-based business rules, and structure the data for serving.
3. **Serving Layer (MongoDB):** Processed metrics are written into a NoSQL document database utilizing an idempotent update strategy to guarantee data integrity.
4. **Machine Learning Pipeline (Scikit-Learn):** A linear regression model trains independently on the historical dataset to compute predictive capacity vectors per server.
5. **API & UI (FastAPI):** A high-performance Python backend exposes the aggregated and forecasted data to a React application for real-time visualization and alert monitoring.

## ✨ Key Features
- **Idempotent Data Processing:** The Spark-MongoDB connector is configured with a strict Upsert strategy (`operationType: update`, bounded by `server_id` and `date`). This guarantees zero data duplication during pipeline retries or manual trigger overlaps.
- **AI-Driven Capacity Forecasting:** The system moves beyond static thresholds. A Scikit-Learn regression model forecasts a continuous 7-day usage trajectory per server, calculating the exact day a node will hit 100% saturation.
- **Automated Orchestration:** The entire flow—from data generation and HDFS ingestion to Spark computation and ML retraining—is wrapped in an automated Bash orchestrator, scheduled via standard Linux Cron.
- **Dual-Line Telemetry Visualization:** The React frontend utilizes Recharts to seamlessly stitch historical data (solid curves) with ML forecasts (dashed curves) on a single, continuous timeline.

## 💻 Technical Stack
* **Big Data & Storage:** Apache Hadoop (HDFS), Apache Spark (PySpark)
* **Database:** MongoDB (PyMongo)
* **Machine Learning:** Scikit-Learn, Pandas, Pickle
* **Backend:** FastAPI, Python 3.10+, JWT Authentication
* **Frontend:** React, Vite, TailwindCSS, Recharts
* **Infrastructure:** Docker, Docker Compose, Bash/Cron

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for local backend development)
- Node.js 18+ (for local frontend development)

### Deployment
1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/storage-optimization-ai.git
   cd storage-optimization-ai
   ```

2. **Spin up the Big Data Infrastructure:**
   Ensure your Docker daemon is running, then initialize the Hadoop, Spark, and MongoDB containers:
   ```bash
   docker-compose up -d
   ```

3. **Start the Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Start the Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## ⚙️ Usage & Automation
The ecosystem is designed to run completely autonomously. 

To run a manual batch cycle:
```bash
chmod +x run_pipeline.sh
./run_pipeline.sh
```

**Automation (Cron):**
To configure the pipeline to ingest new data and retrain the ML models daily at midnight, add the following to your crontab (`crontab -e`):
```bash
0 0 * * * cd /absolute/path/to/project && ./run_pipeline.sh >> pipeline.log 2>&1
```

## 🔮 Future Work & Scalability
To graduate this project to enterprise scale, the following architectural upgrades are recommended:
- **Streaming Ingestion:** Replace batch CSV uploads with Apache Kafka for real-time metric streaming.
- **Advanced Orchestration:** Migrate from Bash/Cron to **Apache Airflow** or **Prefect** for DAG-based execution and robust failure recovery.
- **Deep Learning Forecasting:** Swap the Linear Regression model for an LSTM (Long Short-Term Memory) or Prophet neural network to account for seasonal variations in storage usage.
