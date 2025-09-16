import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import os

default_tracking = "file:/app/mlruns"

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", default_tracking))

# Start an MLflow run
with mlflow.start_run():

    # Load dataset
    data = pd.read_csv(r"C:\Users\Jahnavi Prakash\Downloads\Detect_obstacles_in_roads\Detect_obstacles_in_roads\Data\anomalies.csv")

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
    output_path = "output.csv"
    data.to_csv(output_path, index=False)
    print(f"✅ Results saved to {output_path}")

    # ---- MLflow Logging ----
    # Log parameters
    mlflow.log_param("n_clusters", n_clusters)
    mlflow.log_param("random_state", random_state)

    # Log metrics
    mlflow.log_metric("inertia", kmeans.inertia_)
    try:
        score = silhouette_score(scaled_features, clusters)
        mlflow.log_metric("silhouette_score", score)
    except Exception as e:
        print("⚠️ Could not compute silhouette score:", e)

    # Log model
    mlflow.sklearn.log_model(kmeans, "kmeans_model")

    # Log artifact (output file)
    mlflow.log_artifact(output_path)
