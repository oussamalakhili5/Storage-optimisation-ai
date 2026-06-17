import pandas as pd
import matplotlib.pyplot as plt
# Charger le fichier CSV
data = pd.read_csv("backend/app/data/storage_data.csv")

# Dernière ligne
latest = data.iloc[-1]

# Récupération des valeurs
total_storage = latest["total_storage"]
used_storage = latest["used_storage"]
free_storage = latest["free_storage"]

# Calcul du pourcentage
usage_percentage = (used_storage / total_storage) * 100

# Affichage
print("===== ANALYSE DU STOCKAGE =====")
print(f"Stockage total : {total_storage} GB")
print(f"Stockage utilisé : {used_storage} GB")
print(f"Stockage libre : {free_storage} GB")
print(f"Taux d'utilisation : {usage_percentage:.2f}%")
# Alerte simple
if usage_percentage >= 90:
    print("ALERTE CRITIQUE : Le stockage est presque saturé.")
elif usage_percentage >= 75:
    print("ALERTE WARNING : Le stockage commence à être élevé.")
else:
    print("Stockage normal.")

    # Graphique
plt.plot(data["date"], data["used_storage"], marker='o')

# Titres
plt.title("Évolution du stockage utilisé")
plt.xlabel("Date")
plt.ylabel("Stockage utilisé (GB)")

# Rotation des dates
plt.xticks(rotation=45)

# Affichage
plt.show()