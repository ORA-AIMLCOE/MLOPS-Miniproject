import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import os
import pickle
from datetime import datetime

# ------------------------------
# File paths
# ------------------------------
DATA_PATH = os.getenv("DATA_PATH", "data/anomalies.csv")
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "output.csv")

# Use timestamped model version
MODEL_DIR = os.getenv("MODEL_DIR", "models")
os.makedirs(MODEL_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
MODEL_PATH = os.path.join(MODEL_DIR, f"model_{timestamp}.pkl")

# MLflow tracking
default_tracking = "file:mlruns"
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", default_tracking))
mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "pothole_detection"))

with mlflow.start_run():

    # Load dataset
    data = pd.read_csv(DATA_PATH)

    # Select features
    features = data[["acc_x", "acc_y", "acc_z", "speed_diff", "magnitude", "road_type"]]

    # Scale
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features.fillna(features.mean()))

    # Parameters
    n_clusters = 2
    random_state = 42

    # Clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
    clusters = kmeans.fit_predict(scaled_features)
    data["cluster"] = clusters

    # Map clusters to labels
    cluster_to_class = {0: "probably pothole", 1: "probably speed bump"}
    data["class"] = data["cluster"].map(cluster_to_class)

    # Save output
    data.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Results saved to {OUTPUT_PATH}")

    # Save model as pickle (versioned)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(kmeans, f)
    print(f"✅ Model saved to {MODEL_PATH}")

    # MLflow Logging
    mlflow.log_param("n_clusters", n_clusters)
    mlflow.log_param("random_state", random_state)
    mlflow.log_metric("inertia", kmeans.inertia_)

    try:
        score = silhouette_score(scaled_features, clusters)
        mlflow.log_metric("silhouette_score", score)
    except Exception as e:
        print("⚠️ Could not compute silhouette score:", e)

    # Log models/artifacts in MLflow
    mlflow.sklearn.log_model(kmeans, f"kmeans_model_{timestamp}")
    mlflow.log_artifact(OUTPUT_PATH)
    mlflow.log_artifact(MODEL_PATH)
