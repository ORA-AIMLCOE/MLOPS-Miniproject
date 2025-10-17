import os
import pandas as pd
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from datetime import datetime
import pickle
import json

# ------------------------------
# File paths and configs
# ------------------------------
DATA_PATH = os.getenv("DATA_PATH", "data/anomalies.csv")
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "output.csv")
MODEL_DIR = os.getenv("MODEL_DIR", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
MODEL_PATH = os.path.join(MODEL_DIR, f"model_{timestamp}.pkl")

# MLflow setup
default_tracking = "http://localhost:5000"
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", default_tracking))
mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "pothole_detection"))
MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME", "pothole_kmeans_model")
client = MlflowClient()

# ------------------------------
# Helper: Get latest Production metrics
# ------------------------------
def get_latest_production_metrics():
    """Fetch metrics of the latest Production model safely as floats."""
    try:
        versions = client.search_model_versions(f"name='{MODEL_NAME}'")
        prod_models = [m for m in versions if m.current_stage == "Production"]

        if not prod_models:
            print("No Production model found — first deployment.")
            return None, None, None

        latest_prod = sorted(prod_models, key=lambda m: int(m.version), reverse=True)[0]
        prod_run_id = latest_prod.run_id

        # Fetch metrics and convert to float
        run_metrics = client.get_run(prod_run_id).data.metrics
        prod_sil = float(run_metrics.get("silhouette_score", 0))
        prod_inertia = float(run_metrics.get("inertia", float("inf")))

        print(f"Production Model v{latest_prod.version}: silhouette={prod_sil}, inertia={prod_inertia}")
        return prod_sil, prod_inertia, latest_prod.version

    except Exception as e:
        print(f"Failed to fetch production metrics: {e}")
        return None, None, None


# ------------------------------
# Train + Log + Register + Compare
# ------------------------------
try:
    with mlflow.start_run() as run:
        run_id = run.info.run_id
        print(f"Starting MLflow run: {run_id}")

        # ------------------------------
        # Load and prepare data
        # ------------------------------
        data = pd.read_csv(DATA_PATH)
        features = data[["acc_x", "acc_y", "acc_z", "speed_diff", "magnitude", "road_type"]]
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features.fillna(features.mean()))

        # ------------------------------
        # Train model
        # ------------------------------
        n_clusters = 2
        random_state = 42
        kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
        clusters = kmeans.fit_predict(scaled_features)
        data["cluster"] = clusters
        data["class"] = data["cluster"].map({0: "probably pothole", 1: "probably speed bump"})

        # Save predictions
        data.to_csv(OUTPUT_PATH, index=False)
        print(f"✅ Results saved to {OUTPUT_PATH}")

        # Save local model
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(kmeans, f)
        print(f"✅ Local model saved to {MODEL_PATH}")

        # ------------------------------
        # Compute metrics
        # ------------------------------
        inertia = float(kmeans.inertia_)
        try:
            sil_score = float(silhouette_score(scaled_features, clusters))
        except Exception as e:
            sil_score = 0.0
            print(f"⚠️ Could not compute silhouette score: {e}")

        print(f"📊 New Model Metrics -> Silhouette: {sil_score:.4f}, Inertia: {inertia:.4f}")

        # ------------------------------
        # Log parameters, metrics & model
        # ------------------------------
        mlflow.log_param("n_clusters", n_clusters)
        mlflow.log_param("random_state", random_state)
        mlflow.log_metric("silhouette_score", sil_score)
        mlflow.log_metric("inertia", inertia)

        # Log model + artifacts
        mlflow.sklearn.log_model(kmeans, "model")
        mlflow.log_artifact(OUTPUT_PATH)
        mlflow.log_artifact(MODEL_PATH)

        # ------------------------------
        # Register the model
        # ------------------------------
        model_uri = f"runs:/{run_id}/model"
        print(f"📦 Registering model '{MODEL_NAME}'...")
        registered_model = mlflow.register_model(model_uri=model_uri, name=MODEL_NAME)
        print(f"✅ Model registered: {MODEL_NAME} (version {registered_model.version})")

        # ------------------------------
        # Compare with latest Production model
        # ------------------------------
        prod_sil, prod_inertia, prod_version = get_latest_production_metrics()

        if prod_sil is None:
            target_stage = "Production"
            print("🚀 First model — promoting directly to Production.")
        else:
            better_sil = sil_score > prod_sil
            better_inertia = inertia < prod_inertia

            if better_sil and better_inertia:
                target_stage = "Production"
                print("✅ New model performs better → Promoting to Production.")
            else:
                target_stage = "Staging"
                print("⚠️ New model not better → Moving to Staging.")

        # ------------------------------
        # Transition model stage (safe mode)
        # ------------------------------
        try:
            client.transition_model_version_stage(
                name=MODEL_NAME,
                version=registered_model.version,
                stage=target_stage,
                archive_existing_versions=False  # prevents YAML metric serialization bug
            )
            print(f"📦 Model v{registered_model.version} transitioned to stage: {target_stage}")
            mlflow.log_param("model_stage", target_stage)
        except Exception as e:
            print(f"❌ Stage transition failed: {e}")
            mlflow.log_param("model_stage", "None")

    # ------------------------------
    # Save metrics locally for DVC
    # ------------------------------
    metrics = {
        "model": {
            "silhouette_score": sil_score,
            "inertia": inertia,
            "n_clusters": n_clusters,
            "data_size": len(data),
            "model_version": registered_model.version,
            "stage": target_stage
        }
    }

    with open("model_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("\n✅ Training, logging, and stage transition complete.\n")

except Exception as e:
    print(f"❌ Error in app.py: {e}")
    pd.DataFrame({"error": [str(e)]}).to_csv(OUTPUT_PATH, index=False)

    error_metrics = {
        "model": {
            "error": str(e),
            "silhouette_score": 0,
            "inertia": 0,
            "n_clusters": 0,
            "data_size": 0,
            "model_version": "unknown",
            "stage": "error"
        }
    }

    with open("model_metrics.json", "w") as f:
        json.dump(error_metrics, f, indent=2)
