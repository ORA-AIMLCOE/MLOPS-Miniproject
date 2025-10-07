import pickle
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import subprocess
import os
import glob

# ------------------------------
# Paths
# ------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # folder where this script lives
DATA_PATH = os.path.join(BASE_DIR, "data/anomalies.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# ------------------------------
# Thresholds
# ------------------------------
SIL_THRESHOLD = 0.5
INERTIA_THRESHOLD = 1000

# ------------------------------
# Load new data
# ------------------------------
data = pd.read_csv(DATA_PATH)
features = data[["acc_x", "acc_y", "acc_z", "speed_diff", "magnitude", "road_type"]]
scaled_features = StandardScaler().fit_transform(features.fillna(features.mean()))

# ------------------------------
# Find latest model
# ------------------------------
model_files = sorted(glob.glob(os.path.join(MODEL_DIR, "model_*.pkl")), reverse=True)

if model_files:
    latest_model = model_files[0]
    print(f"ℹ️ Using latest model: {latest_model}")
    with open(latest_model, "rb") as f:
        kmeans = pickle.load(f)

    # Predict on new data
    clusters = kmeans.predict(scaled_features)

    # Compute metrics
    try:
        sil_score = silhouette_score(scaled_features, clusters)
        inertia = kmeans.inertia_
        print(f"ℹ️ Silhouette Score: {sil_score:.4f}, Inertia: {inertia:.4f}")

        if sil_score < SIL_THRESHOLD or inertia > INERTIA_THRESHOLD:
            print("⚠️ Metrics below threshold → retraining model")
            subprocess.run(["python", os.path.join(BASE_DIR, "app.py")], check=True)
        else:
            print("✅ Metrics okay → skipping retraining")

    except Exception as e:
        print("⚠️ Could not compute metrics, retraining anyway:", e)
        subprocess.run(["python", os.path.join(BASE_DIR, "app.py")], check=True)

else:
    print("ℹ️ No existing model → training for the first time")
    subprocess.run(["python", os.path.join(BASE_DIR, "app.py")], check=True)
