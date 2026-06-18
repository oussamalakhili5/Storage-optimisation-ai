import os
import pickle
import pandas as pd
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

from app.database import server_metrics

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "data", "storage_model.pkl")


def train_model():
    """
    Reads historical metrics from MongoDB, trains a Linear Regression model 
    per server, and saves the dictionary of models as a .pkl file.
    """
    cursor = server_metrics.find().sort("date", 1)
    df = pd.DataFrame(list(cursor))
    
    if df.empty:
        raise ValueError("Insufficient data in MongoDB to train the model.")
        
    models = {}
    
    # We train an independent Linear Regression curve for each server
    for server_id, group in df.groupby("server_id"):
        # Create a linear time index: 1, 2, 3...
        group = group.sort_values("date").reset_index(drop=True)
        group["day_number"] = group.index + 1
        
        X = group[["day_number"]]
        y = group["used_storage"]
        
        model = LinearRegression()
        model.fit(X, y)
        models[server_id] = model
        
    # Ensure data directory exists
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    # Save models
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(models, f)
        
    return {"status": "success", "models_trained": len(models)}


def predict_future(server_id: str, days: int = 7):
    """
    Loads the .pkl model and predicts the next X days of storage_used 
    for the given server based on its historical trend.
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Model file 'storage_model.pkl' is missing. Please train the model first.")
        
    with open(MODEL_PATH, "rb") as f:
        models = pickle.load(f)
        
    if server_id not in models:
        raise ValueError(f"No trained model found for server {server_id}. Ensure it has historical data and the model was trained.")
        
    model = models[server_id]
    
    # Fetch historical data to find the last point of reference
    cursor = server_metrics.find({"server_id": server_id}).sort("date", 1)
    records = list(cursor)
    
    if not records:
        raise ValueError(f"No historical data found for server {server_id} in MongoDB.")
        
    last_day_number = len(records)
    last_record = records[-1]
    
    try:
        last_date = datetime.strptime(last_record["date"], "%Y-%m-%d")
    except ValueError:
        # Fallback if date is not properly formatted
        last_date = datetime.utcnow()
        
    total_storage = last_record.get("total_storage", 0)
    predictions = []
    
    for i in range(1, days + 1):
        future_day_number = last_day_number + i
        
        # model.predict returns a numpy array, we extract the first element
        pred_used = model.predict(pd.DataFrame({"day_number": [future_day_number]}))[0]
        
        # Don't predict negative storage
        pred_used = max(0, pred_used)
        
        pred_date = last_date + timedelta(days=i)
        
        utilization = (pred_used / total_storage) * 100 if total_storage > 0 else 0
        
        predictions.append({
            "date": pred_date.strftime("%Y-%m-%d"),
            "predicted_used_storage": round(pred_used, 2),
            "total_storage": total_storage,
            "predicted_utilization_percent": round(utilization, 2)
        })
        
    return predictions