# Storage Optimization AI

A full-stack application for analyzing storage data, detecting anomalies, making predictions, and generating recommendations using machine learning.

## Project Structure

- **Backend**: Python Flask API with ML modules for storage analysis
- **Frontend**: React + Vite application for visualizations
- **Database**: PostgreSQL for data persistence
- **Big Data**: Hadoop (HDFS) for distributed storage analysis

## Requirements to Run This Project

### Option 1: Using Docker Compose (Recommended - No Ubuntu needed)

- **Docker Desktop** (includes Docker Engine and Docker Compose)
- **Windows 10/11** with Hyper-V enabled

### Option 2: Local Development

- **Python 3.10+**
- **Node.js 18+** and npm
- **PostgreSQL 16** (for database)
- **Docker** (optional, for Hadoop services)

## Installation

### Using Docker Compose (Recommended)

1. **Install Docker Desktop**
   - Download from [Docker Website](https://www.docker.com/products/docker-desktop)
   - Install and ensure it's running

2. **Clone and Navigate to Project**
   ```bash
   cd storage-optimization-ai
   ```

3. **Start All Services**
   ```bash
   docker-compose up -d
   ```
   This will start:
   - Backend API (http://localhost:8000)
   - PostgreSQL Database (localhost:5432)
   - Hadoop NameNode (http://localhost:9870)
   - Frontend (http://localhost:5173)

### Local Development Setup

#### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

#### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## Running the Application

### Using Docker Compose
```bash
# Start services in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Local Development
- **Backend**: Runs on `http://localhost:8000`
- **Frontend**: Runs on `http://localhost:5173` (after `npm run dev`)

## API Endpoints

- **Auth**: `/api/auth/*`
- **Storage**: `/api/storage/*`
- **Alerts**: `/api/alerts/*`
- **Predictions**: `/api/predictions/*`
- **Reports**: `/api/reports/*`

## Database Configuration

Default credentials (in docker-compose.yml):
- **Host**: localhost:5432
- **User**: admin
- **Password**: admin123
- **Database**: storage_db

## Technologies Used

### Backend
- Flask (API Framework)
- SQLAlchemy (ORM)
- Scikit-learn (ML)
- Pandas (Data Analysis)

### Frontend
- React 19
- Vite (Build Tool)
- Recharts (Charting)

### Infrastructure
- PostgreSQL (Database)
- Hadoop HDFS (Distributed Storage)
- Docker & Docker Compose

## Important Notes

### Do You Need Ubuntu/WSL on Windows?

**Short Answer: NO, it's not obligatory.**

**With Docker Desktop**: You don't need Ubuntu/WSL. Docker Desktop on Windows handles Linux containerization internally using Hyper-V (Windows Pro/Enterprise) or WSL2 (Windows Home). All services run in containers.

**Optional - When WSL/Ubuntu Might Be Useful**:
- If you want to develop directly on Linux without containers
- If you prefer a Linux terminal environment
- For advanced Hadoop/distributed system work
- If you have Windows Home edition and want better Docker performance via WSL2

**Recommended Approach for Windows**:
1. Use Docker Desktop with Docker Compose (no Ubuntu needed)
2. Or optionally enable WSL2 in Docker Desktop for better performance

## Troubleshooting

**Port Already in Use**:
```bash
# Change ports in docker-compose.yml if needed
```

**Database Connection Error**:
- Ensure PostgreSQL service is running
- Check credentials in configuration

**Docker Issues**:
- Ensure Docker Desktop is running
- Check Docker resources/memory allocation

## Development

### Running Tests
```bash
cd backend
python test_register.py
```

### Training ML Models
See `notebooks/model_training.ipynb` for model development and training procedures.

## License

[Add License Info]

## Support

For issues or questions, please check the documentation in the `/docs` folder.
