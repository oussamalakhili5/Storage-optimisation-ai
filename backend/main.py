import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
from pathlib import Path
from hdfs import InsecureClient
from io import StringIO

from app.database import Base, engine, SessionLocal
from app.models.storage_record import StorageRecord
from app.models.user import User
from app.routes.auth_routes import router as auth_router
from auth.jwt_manager import init_jwt

# Load environment variables from .env file
load_dotenv()


# =========================
# Création de l'application
# =========================

app = FastAPI(
    title="Storage Optimization AI API",
    description="API pour l'optimisation dynamique des ressources de stockage avec Machine Learning et Hadoop HDFS",
    version="1.0.0"
)

# Initialize JWT authentication
init_jwt(app)


# =========================
# Création des tables
# =========================

Base.metadata.create_all(bind=engine)


# =========================
# CORS pour React
# =========================

# Get allowed origins from environment variable
ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# =========================
# Routes Auth
# =========================

app.include_router(auth_router)


# =========================
# Chemins CSV et HDFS
# =========================

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "app" / "data" / "storage_data.csv"

HDFS_URL = os.getenv("HDFS_URL", "http://localhost:9870")
HDFS_FILE_PATH = os.getenv("HDFS_FILE_PATH", "/data/storage/storage_data.csv")
HDFS_USER = os.getenv("HDFS_USER", "root")


# =========================
# Client HDFS
# =========================

def get_hdfs_client():
    """
    Créer une connexion vers Hadoop HDFS via WebHDFS.
    """
    return InsecureClient(HDFS_URL, user=HDFS_USER)


def load_storage_data_from_hdfs():
    """
    Charger le dataset depuis Hadoop HDFS puis appliquer le nettoyage.
    """
    client = get_hdfs_client()

    try:
        status = client.status(HDFS_FILE_PATH, strict=False)

        if status is None:
            raise HTTPException(
                status_code=404,
                detail=f"Fichier introuvable dans HDFS : {HDFS_FILE_PATH}"
            )

        with client.read(HDFS_FILE_PATH, encoding="utf-8") as reader:
            csv_content = reader.read()

        data = pd.read_csv(StringIO(csv_content))
        data = clean_storage_data(data)

        if data.empty:
            raise HTTPException(
                status_code=400,
                detail="Le dataset HDFS est vide après nettoyage."
            )

        return data

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la lecture depuis HDFS : {str(e)}"
        )


# =========================
# Nettoyage des données
# =========================

def clean_storage_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoyer les données du dataset enrichi.

    Colonnes attendues :
    - server_id
    - date
    - total_storage
    - used_storage
    - free_storage
    - cpu_usage
    - memory_usage
    - read_frequency
    - write_frequency
    """

    required_columns = [
        "server_id",
        "date",
        "total_storage",
        "used_storage",
        "free_storage",
        "cpu_usage",
        "memory_usage",
        "read_frequency",
        "write_frequency",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Colonnes manquantes dans le dataset : {missing_columns}"
        )

    data = data[required_columns].copy()

    # Supprimer les doublons et valeurs manquantes
    data = data.drop_duplicates()
    data = data.dropna()

    # Nettoyer server_id
    data["server_id"] = data["server_id"].astype(str).str.strip()
    data = data[data["server_id"] != ""]

    # Conversion date
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data = data.dropna(subset=["date"])

    # Conversion numérique
    numeric_columns = [
        "total_storage",
        "used_storage",
        "free_storage",
        "cpu_usage",
        "memory_usage",
        "read_frequency",
        "write_frequency",
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.dropna()

    # Supprimer les valeurs incohérentes
    data = data[data["total_storage"] > 0]
    data = data[data["used_storage"] >= 0]
    data = data[data["cpu_usage"] >= 0]
    data = data[data["memory_usage"] >= 0]
    data = data[data["read_frequency"] >= 0]
    data = data[data["write_frequency"] >= 0]

    # Limiter CPU et RAM à 100%
    data.loc[data["cpu_usage"] > 100, "cpu_usage"] = 100
    data.loc[data["memory_usage"] > 100, "memory_usage"] = 100

    # Corriger used_storage si supérieur à total_storage
    data.loc[
        data["used_storage"] > data["total_storage"],
        "used_storage"
    ] = data["total_storage"]

    # Recalculer free_storage
    data["free_storage"] = data["total_storage"] - data["used_storage"]

    # Trier par serveur et date
    data = data.sort_values(by=["server_id", "date"])

    # Reconvertir date en string
    data["date"] = data["date"].dt.strftime("%Y-%m-%d")

    data = data.reset_index(drop=True)

    return data


# =========================
# Charger CSV local
# =========================

def load_storage_data():
    """
    Charger le dataset local depuis CSV.
    """
    if not CSV_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Fichier CSV introuvable : {CSV_PATH}"
        )

    data = pd.read_csv(CSV_PATH)
    data = clean_storage_data(data)

    if data.empty:
        raise HTTPException(
            status_code=400,
            detail="Le dataset est vide après nettoyage."
        )

    return data


# =========================
# Fonctions métier
# =========================

def classify_server(usage_percentage):
    if usage_percentage < 50:
        return "normal"
    elif usage_percentage < 80:
        return "chargé"
    else:
        return "critique"


def generate_alert(usage_percentage):
    if usage_percentage >= 90:
        return "ALERTE CRITIQUE : stockage presque saturé"
    elif usage_percentage >= 80:
        return "ALERTE : serveur critique"
    elif usage_percentage >= 50:
        return "WARNING : stockage élevé"
    else:
        return "Stockage normal"


def generate_recommendation(usage_percentage):
    if usage_percentage >= 90:
        return "Ajouter de la capacité ou migrer une partie des données vers un autre serveur."
    elif usage_percentage >= 80:
        return "Archiver les anciennes données et surveiller le serveur."
    elif usage_percentage >= 50:
        return "Optimiser la répartition des données et nettoyer les fichiers inutiles."
    else:
        return "Aucune action urgente. Continuer la surveillance normale."


# =========================
# Home
# =========================

@app.get("/")
def home():
    return {
        "message": "API Storage Optimization AI fonctionne correctement avec FastAPI, PostgreSQL, Docker et Hadoop HDFS"
    }


# =========================
# Routes Hadoop HDFS
# =========================

@app.get("/storage/hdfs-status")
def hdfs_status():
    """
    Vérifier la connexion à Hadoop HDFS et l'existence du dataset.
    """
    client = get_hdfs_client()

    try:
        status = client.status(HDFS_FILE_PATH, strict=False)

        if status is None:
            return {
                "hdfs_connected": True,
                "file_exists": False,
                "hdfs_path": HDFS_FILE_PATH,
                "message": "Connexion HDFS réussie, mais fichier introuvable."
            }

        return {
            "hdfs_connected": True,
            "file_exists": True,
            "hdfs_path": HDFS_FILE_PATH,
            "file_size": status["length"],
            "message": "Fichier trouvé dans Hadoop HDFS."
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de connexion à Hadoop HDFS : {str(e)}"
        )


@app.get("/storage/hdfs-preview")
def hdfs_preview():
    """
    Lire et afficher un aperçu des données stockées dans Hadoop HDFS.
    """
    data = load_storage_data_from_hdfs()

    return {
        "source": "Hadoop HDFS",
        "hdfs_path": HDFS_FILE_PATH,
        "rows": len(data),
        "columns": list(data.columns),
        "preview": data.head(10).to_dict(orient="records")
    }


@app.post("/storage/import-hdfs")
def import_hdfs_to_db():
    """
    Importer les données depuis Hadoop HDFS vers PostgreSQL.
    """
    data = load_storage_data_from_hdfs()

    db = SessionLocal()

    try:
        db.query(StorageRecord).delete()

        for _, row in data.iterrows():
            record = StorageRecord(
                server_id=row["server_id"],
                date=row["date"],
                total_storage=float(row["total_storage"]),
                used_storage=float(row["used_storage"]),
                free_storage=float(row["free_storage"]),
                cpu_usage=float(row["cpu_usage"]),
                memory_usage=float(row["memory_usage"]),
                read_frequency=float(row["read_frequency"]),
                write_frequency=float(row["write_frequency"])
            )

            db.add(record)

        db.commit()

        return {
            "message": "Données importées depuis Hadoop HDFS vers PostgreSQL avec succès",
            "source": "Hadoop HDFS",
            "hdfs_path": HDFS_FILE_PATH,
            "rows_imported": len(data)
        }

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erreur import HDFS vers PostgreSQL : {str(e)}"
        )

    finally:
        db.close()


# =========================
# Aperçu nettoyage CSV local
# =========================

@app.get("/storage/clean-preview")
def clean_preview():
    raw_data = pd.read_csv(CSV_PATH)
    cleaned_data = clean_storage_data(raw_data)

    return {
        "source": "CSV local",
        "raw_rows": len(raw_data),
        "cleaned_rows": len(cleaned_data),
        "removed_rows": len(raw_data) - len(cleaned_data),
        "columns": list(cleaned_data.columns),
        "preview": cleaned_data.to_dict(orient="records")
    }


# =========================
# État actuel du stockage
# =========================

@app.get("/storage/status")
def storage_status():
    data = load_storage_data()

    latest = data.sort_values(by=["date"]).iloc[-1]

    total_storage = float(latest["total_storage"])
    used_storage = float(latest["used_storage"])
    free_storage = float(latest["free_storage"])

    usage_percentage = (used_storage / total_storage) * 100

    return {
        "server_id": latest["server_id"],
        "date": latest["date"],
        "total_storage": total_storage,
        "used_storage": used_storage,
        "free_storage": free_storage,
        "cpu_usage": float(latest["cpu_usage"]),
        "memory_usage": float(latest["memory_usage"]),
        "read_frequency": float(latest["read_frequency"]),
        "write_frequency": float(latest["write_frequency"]),
        "usage_percentage": round(usage_percentage, 2),
        "server_status": classify_server(usage_percentage),
        "alert": generate_alert(usage_percentage),
        "recommendation": generate_recommendation(usage_percentage)
    }


# =========================
# Historique complet
# =========================

@app.get("/storage/history")
def storage_history():
    data = load_storage_data()

    records = []

    for _, row in data.iterrows():
        total_storage = float(row["total_storage"])
        used_storage = float(row["used_storage"])
        free_storage = float(row["free_storage"])

        usage_percentage = (used_storage / total_storage) * 100

        records.append({
            "server_id": row["server_id"],
            "date": row["date"],
            "total_storage": total_storage,
            "used_storage": used_storage,
            "free_storage": free_storage,
            "cpu_usage": float(row["cpu_usage"]),
            "memory_usage": float(row["memory_usage"]),
            "read_frequency": float(row["read_frequency"]),
            "write_frequency": float(row["write_frequency"]),
            "usage_percentage": round(usage_percentage, 2),
            "server_status": classify_server(usage_percentage),
            "alert": generate_alert(usage_percentage),
            "recommendation": generate_recommendation(usage_percentage)
        })

    return records


# =========================
# Prédiction ML
# =========================

@app.get("/storage/prediction")
def storage_prediction():
    data = load_storage_data()

    predictions = []

    for server_id, server_data in data.groupby("server_id"):
        server_data = server_data.sort_values(by="date").copy()
        server_data["day_number"] = range(1, len(server_data) + 1)

        if len(server_data) < 2:
            continue

        X = server_data[["day_number"]]
        y = server_data["used_storage"]

        model = LinearRegression()
        model.fit(X, y)

        next_day = pd.DataFrame({
            "day_number": [len(server_data) + 1]
        })

        prediction = model.predict(next_day)[0]

        latest_total_storage = float(server_data.iloc[-1]["total_storage"])
        predicted_usage_percentage = (prediction / latest_total_storage) * 100

        predictions.append({
            "server_id": server_id,
            "next_day_prediction": round(float(prediction), 2),
            "predicted_usage_percentage": round(float(predicted_usage_percentage), 2),
            "predicted_status": classify_server(predicted_usage_percentage),
            "alert": generate_alert(predicted_usage_percentage),
            "recommendation": generate_recommendation(predicted_usage_percentage)
        })

    return predictions


# =========================
# Détection anomalies
# =========================

@app.get("/storage/anomalies")
def storage_anomalies():
    data = load_storage_data()

    if len(data) < 2:
        return []

    model = IsolationForest(
        contamination=0.15,
        random_state=42
    )

    features = [
        "used_storage",
        "cpu_usage",
        "memory_usage",
        "read_frequency",
        "write_frequency",
    ]

    data["anomaly"] = model.fit_predict(data[features])

    anomalies = data[data["anomaly"] == -1]

    result = []

    for _, row in anomalies.iterrows():
        total_storage = float(row["total_storage"])
        used_storage = float(row["used_storage"])
        free_storage = float(row["free_storage"])
        usage_percentage = (used_storage / total_storage) * 100

        result.append({
            "server_id": row["server_id"],
            "date": row["date"],
            "total_storage": total_storage,
            "used_storage": used_storage,
            "free_storage": free_storage,
            "cpu_usage": float(row["cpu_usage"]),
            "memory_usage": float(row["memory_usage"]),
            "read_frequency": float(row["read_frequency"]),
            "write_frequency": float(row["write_frequency"]),
            "usage_percentage": round(usage_percentage, 2),
            "server_status": classify_server(usage_percentage),
            "anomaly": True,
            "alert": "Anomalie détectée dans l'utilisation du stockage",
            "recommendation": generate_recommendation(usage_percentage)
        })

    return result


# =========================
# Alertes
# =========================

@app.get("/storage/alerts")
def storage_alerts():
    data = load_storage_data()

    alerts = []

    for _, row in data.iterrows():
        total_storage = float(row["total_storage"])
        used_storage = float(row["used_storage"])
        usage_percentage = (used_storage / total_storage) * 100

        if usage_percentage >= 50:
            alerts.append({
                "server_id": row["server_id"],
                "date": row["date"],
                "usage_percentage": round(usage_percentage, 2),
                "cpu_usage": float(row["cpu_usage"]),
                "memory_usage": float(row["memory_usage"]),
                "server_status": classify_server(usage_percentage),
                "alert": generate_alert(usage_percentage),
                "recommendation": generate_recommendation(usage_percentage)
            })

    return alerts


# =========================
# Recommandations
# =========================

@app.get("/storage/recommendations")
def storage_recommendations():
    data = load_storage_data()

    recommendations = []

    for _, row in data.iterrows():
        total_storage = float(row["total_storage"])
        used_storage = float(row["used_storage"])
        usage_percentage = (used_storage / total_storage) * 100

        recommendations.append({
            "server_id": row["server_id"],
            "date": row["date"],
            "usage_percentage": round(usage_percentage, 2),
            "server_status": classify_server(usage_percentage),
            "recommendation": generate_recommendation(usage_percentage)
        })

    return recommendations


# =========================
# Statistiques globales
# =========================

@app.get("/storage/statistics")
def storage_statistics():
    data = load_storage_data()

    data["usage_percentage"] = (
        data["used_storage"] / data["total_storage"]
    ) * 100

    total_records = len(data)
    total_servers = data["server_id"].nunique()

    normal_count = len(data[data["usage_percentage"] < 50])
    loaded_count = len(
        data[
            (data["usage_percentage"] >= 50)
            & (data["usage_percentage"] < 80)
        ]
    )
    critical_count = len(data[data["usage_percentage"] >= 80])

    return {
        "total_records": total_records,
        "total_servers": total_servers,
        "average_used_storage": round(float(data["used_storage"].mean()), 2),
        "max_used_storage": round(float(data["used_storage"].max()), 2),
        "min_used_storage": round(float(data["used_storage"].min()), 2),
        "average_usage_percentage": round(float(data["usage_percentage"].mean()), 2),
        "average_cpu_usage": round(float(data["cpu_usage"].mean()), 2),
        "average_memory_usage": round(float(data["memory_usage"].mean()), 2),
        "normal_servers": normal_count,
        "loaded_servers": loaded_count,
        "critical_servers": critical_count
    }


# =========================
# Rapport résumé
# =========================

@app.get("/storage/report")
def storage_report():
    data = load_storage_data()

    data["usage_percentage"] = (
        data["used_storage"] / data["total_storage"]
    ) * 100

    latest = data.sort_values(by=["date"]).iloc[-1]

    critical_count = len(data[data["usage_percentage"] >= 80])
    alert_count = len(data[data["usage_percentage"] >= 50])

    return {
        "project_name": "Optimisation Dynamique des Ressources de Stockage avec l'Apprentissage Automatique",
        "current_server": latest["server_id"],
        "current_date": latest["date"],
        "current_usage_percentage": round(float(latest["usage_percentage"]), 2),
        "current_status": classify_server(float(latest["usage_percentage"])),
        "current_alert": generate_alert(float(latest["usage_percentage"])),
        "current_recommendation": generate_recommendation(float(latest["usage_percentage"])),
        "total_servers": int(data["server_id"].nunique()),
        "total_alerts": alert_count,
        "total_critical_cases": critical_count,
        "summary": "Le système analyse plusieurs serveurs, détecte les risques de saturation et propose des recommandations d'optimisation."
    }


# =========================
# Import CSV local vers PostgreSQL
# =========================

@app.post("/storage/import-csv")
def import_csv_to_db():
    data = load_storage_data()

    db = SessionLocal()

    try:
        db.query(StorageRecord).delete()

        for _, row in data.iterrows():
            record = StorageRecord(
                server_id=row["server_id"],
                date=row["date"],
                total_storage=float(row["total_storage"]),
                used_storage=float(row["used_storage"]),
                free_storage=float(row["free_storage"]),
                cpu_usage=float(row["cpu_usage"]),
                memory_usage=float(row["memory_usage"]),
                read_frequency=float(row["read_frequency"]),
                write_frequency=float(row["write_frequency"])
            )

            db.add(record)

        db.commit()

        return {
            "message": "CSV local enrichi nettoyé puis importé avec succès dans PostgreSQL",
            "source": "CSV local",
            "rows_imported": len(data)
        }

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erreur import CSV local vers PostgreSQL : {str(e)}"
        )

    finally:
        db.close()


# =========================
# Afficher données PostgreSQL
# =========================

@app.get("/storage/db-records")
def get_db_records():
    db = SessionLocal()

    try:
        records = db.query(StorageRecord).all()

        return [
            {
                "id": record.id,
                "server_id": record.server_id,
                "date": record.date,
                "total_storage": record.total_storage,
                "used_storage": record.used_storage,
                "free_storage": record.free_storage,
                "cpu_usage": record.cpu_usage,
                "memory_usage": record.memory_usage,
                "read_frequency": record.read_frequency,
                "write_frequency": record.write_frequency
            }
            for record in records
        ]

    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
