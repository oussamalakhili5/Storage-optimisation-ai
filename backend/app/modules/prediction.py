import pandas as pd
from sklearn.linear_model import LinearRegression

# Charger les données
data = pd.read_csv("backend/app/data/storage_data.csv")

# Transformer les dates en nombres simples : 1, 2, 3, ...
data["day_number"] = range(1, len(data) + 1)

# Variables
X = data[["day_number"]]
y = data["used_storage"]

# Création du modèle IA
model = LinearRegression()
model.fit(X, y)

# Prédire le jour suivant
next_day = pd.DataFrame({"day_number": [len(data) + 1]})
prediction = model.predict(next_day)

print("===== PRÉDICTION IA =====")
print(f"Stockage prévu pour le prochain jour : {prediction[0]:.2f} GB")