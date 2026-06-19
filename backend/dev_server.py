"""
Standalone Development Server
==============================
A self-contained FastAPI server that works WITHOUT MongoDB, Docker, or HDFS.
- Users are stored in a local JSON file (users_db.json)
- Storage data is loaded from the CSV file in app/data/
- All endpoints the frontend needs are implemented here

Usage:
    cd backend
    uvicorn dev_server:app --reload --port 8000
"""

import os
import json
import hashlib
import hmac
import base64
import re
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ========================
# Config
# ========================

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "app" / "data" / "storage_data.csv"
USERS_DB_PATH = BASE_DIR / "users_db.json"
SECRET_KEY = "dev-secret-key-storage-optimization-ai"

# ========================
# App
# ========================

app = FastAPI(
    title="Storage Optimization AI API (Dev)",
    description="Development server - no MongoDB required",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)


# ========================
# Simple JSON user store
# ========================

def load_users() -> dict:
    if USERS_DB_PATH.exists():
        with open(USERS_DB_PATH, "r") as f:
            return json.load(f)
    return {}


def save_users(users: dict):
    with open(USERS_DB_PATH, "w") as f:
        json.dump(users, f, indent=2)


def hash_password(password: str) -> str:
    """Simple SHA-256 password hash (fine for dev)."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_password(plain), hashed)


def create_token(user_id: str, username: str, email: str) -> str:
    """Create a simple base64 JWT-like token (stateless, dev only)."""
    payload = json.dumps({
        "user_id": user_id,
        "username": username,
        "email": email,
        "exp": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    })
    return base64.b64encode(payload.encode()).decode()


# ========================
# Pydantic models
# ========================

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    email: str


class AuthResponse(BaseModel):
    user: UserOut
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ========================
# Auth Routes  (/api/...)
# ========================

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@app.post("/api/register/", response_model=AuthResponse, status_code=201)
def register(data: RegisterRequest):
    if not EMAIL_REGEX.match(data.email):
        raise HTTPException(status_code=400, detail="Email invalide")

    users = load_users()
    email_lower = data.email.lower()

    # Check duplicates
    for uid, u in users.items():
        if u["email"] == email_lower:
            raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
        if u["username"].lower() == data.username.lower():
            raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris")

    # Create user
    user_id = hashlib.md5(f"{email_lower}{datetime.utcnow().isoformat()}".encode()).hexdigest()
    users[user_id] = {
        "id": user_id,
        "username": data.username,
        "email": email_lower,
        "password_hash": hash_password(data.password),
        "created_at": datetime.utcnow().isoformat()
    }
    save_users(users)

    token = create_token(user_id, data.username, email_lower)
    return {
        "user": {"id": user_id, "username": data.username, "email": email_lower},
        "access_token": token,
        "refresh_token": token,
        "token_type": "bearer"
    }


@app.post("/api/login/", response_model=AuthResponse)
def login(data: LoginRequest):
    users = load_users()
    email_lower = data.email.lower()

    user = None
    for uid, u in users.items():
        if u["email"] == email_lower:
            user = u
            break

    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    token = create_token(user["id"], user["username"], email_lower)
    return {
        "user": {"id": user["id"], "username": user["username"], "email": email_lower},
        "access_token": token,
        "refresh_token": token,
        "token_type": "bearer"
    }


# ========================
# Load CSV data
# ========================

def load_csv() -> pd.DataFrame:
    if CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH)
        # Add usage_percentage column
        df["usage_percentage"] = (df["used_storage"] / df["total_storage"] * 100).round(1)
        # Add server_status
        def get_status(pct):
            if pct >= 85:
                return "critique"
            elif pct >= 65:
                return "chargé"
            return "normal"
        df["server_status"] = df["usage_percentage"].apply(get_status)
        # Add alert and recommendation
        def get_alert(row):
            if row["server_status"] == "critique":
                return f"⚠️ Serveur {row['server_id']} - Stockage critique ({row['usage_percentage']}%)"
            elif row["server_status"] == "chargé":
                return f"⚡ Serveur {row['server_id']} - Stockage chargé ({row['usage_percentage']}%)"
            return ""
        def get_recommendation(row):
            if row["server_status"] == "critique":
                return "Libérer immédiatement de l'espace ou augmenter la capacité"
            elif row["server_status"] == "chargé":
                return "Planifier une extension de capacité"
            return "Aucune action requise"
        df["alert"] = df.apply(get_alert, axis=1)
        df["recommendation"] = df.apply(get_recommendation, axis=1)
        return df
    return pd.DataFrame()


# ========================
# Storage Routes  (/storage/...)
# ========================

@app.get("/storage/status")
def storage_status():
    df = load_csv()
    if df.empty:
        raise HTTPException(status_code=404, detail="Aucune donnée disponible")

    latest = df.sort_values("date").groupby("server_id").last().reset_index()
    row = latest.iloc[0]
    return {
        "server_id": row["server_id"],
        "date": row["date"],
        "total_storage": int(row["total_storage"]),
        "used_storage": int(row["used_storage"]),
        "free_storage": int(row["free_storage"]),
        "usage_percentage": float(row["usage_percentage"]),
        "cpu_usage": int(row["cpu_usage"]),
        "memory_usage": int(row["memory_usage"]),
        "read_frequency": int(row["read_frequency"]),
        "write_frequency": int(row["write_frequency"]),
        "server_status": row["server_status"],
        "alert": row["alert"],
        "recommendation": row["recommendation"]
    }


@app.get("/storage/history")
def storage_history():
    df = load_csv()
    if df.empty:
        return []
    return df.to_dict(orient="records")


@app.get("/storage/prediction")
def storage_prediction():
    """Simple linear prediction for next day per server."""
    df = load_csv()
    if df.empty:
        return []

    predictions = []
    for server_id, group in df.groupby("server_id"):
        group = group.sort_values("date").reset_index(drop=True)
        n = len(group)
        if n < 2:
            continue

        # Simple linear regression on used_storage
        x = np.arange(n)
        y = group["used_storage"].values
        slope = np.polyfit(x, y, 1)[0]
        last_used = y[-1]
        next_used = max(0, last_used + slope)
        total = group["total_storage"].iloc[0]
        predicted_pct = round(min(100, next_used / total * 100), 1)

        if predicted_pct >= 85:
            pred_status = "critique"
            rec = "Libérer de l'espace immédiatement"
        elif predicted_pct >= 65:
            pred_status = "chargé"
            rec = "Planifier une extension"
        else:
            pred_status = "normal"
            rec = "Aucune action requise"

        predictions.append({
            "server_id": server_id,
            "next_day_prediction": round(float(next_used), 1),
            "predicted_usage_percentage": predicted_pct,
            "predicted_status": pred_status,
            "recommendation": rec
        })

    return predictions


@app.get("/storage/anomalies")
def storage_anomalies():
    """Detect anomalies: records where usage jumped > 15% in one day per server."""
    df = load_csv()
    if df.empty:
        return []

    anomalies = []
    for server_id, group in df.groupby("server_id"):
        group = group.sort_values("date").reset_index(drop=True)
        for i in range(1, len(group)):
            prev_pct = group.iloc[i - 1]["usage_percentage"]
            curr_pct = group.iloc[i]["usage_percentage"]
            if curr_pct - prev_pct >= 10:
                row = group.iloc[i]
                anomalies.append({
                    "server_id": row["server_id"],
                    "date": row["date"],
                    "used_storage": int(row["used_storage"]),
                    "usage_percentage": float(row["usage_percentage"]),
                    "cpu_usage": int(row["cpu_usage"]),
                    "memory_usage": int(row["memory_usage"]),
                    "read_frequency": int(row["read_frequency"]),
                    "write_frequency": int(row["write_frequency"]),
                    "recommendation": row["recommendation"]
                })

    return anomalies


@app.get("/storage/alerts")
def storage_alerts():
    df = load_csv()
    if df.empty:
        return []
    alerts = df[df["server_status"].isin(["critique", "chargé"])].copy()
    return alerts.to_dict(orient="records")


@app.get("/storage/recommendations")
def storage_recommendations():
    df = load_csv()
    if df.empty:
        return []
    cols = ["server_id", "date", "usage_percentage", "server_status", "recommendation"]
    return df[cols].to_dict(orient="records")


@app.get("/storage/statistics")
def storage_statistics():
    df = load_csv()
    if df.empty:
        return {}

    latest = df.sort_values("date").groupby("server_id").last().reset_index()
    return {
        "total_servers": int(latest["server_id"].nunique()),
        "total_records": int(len(df)),
        "average_usage_percentage": round(float(latest["usage_percentage"].mean()), 1),
        "average_cpu_usage": round(float(latest["cpu_usage"].mean()), 1),
        "average_memory_usage": round(float(latest["memory_usage"].mean()), 1),
        "critical_servers": int((latest["server_status"] == "critique").sum()),
        "loaded_servers": int((latest["server_status"] == "chargé").sum()),
        "normal_servers": int((latest["server_status"] == "normal").sum()),
    }


@app.get("/storage/report")
def storage_report():
    df = load_csv()
    if df.empty:
        return {}

    latest = df.sort_values("date").groupby("server_id").last().reset_index()
    row = latest.iloc[0]
    alerts_count = int((df["server_status"].isin(["critique", "chargé"])).sum())
    critical_count = int((latest["server_status"] == "critique").sum())

    return {
        "project_name": "Storage Optimization AI",
        "current_server": row["server_id"],
        "current_date": row["date"],
        "current_usage_percentage": float(row["usage_percentage"]),
        "current_status": row["server_status"],
        "total_servers": int(latest["server_id"].nunique()),
        "total_alerts": alerts_count,
        "total_critical_cases": critical_count,
        "summary": f"Rapport généré le {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC. "
                   f"{int(latest['server_id'].nunique())} serveurs surveillés. "
                   f"{critical_count} cas critiques détectés."
    }


# ========================
# Root & Health
# ========================

@app.get("/")
def root():
    return {"message": "Storage Optimization AI Dev Server", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy", "mode": "development (no-db)"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("dev_server:app", host="0.0.0.0", port=8000, reload=True)
