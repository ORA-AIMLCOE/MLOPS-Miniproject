import os
import pandas as pd
import numpy as np
import json
import yaml
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import subprocess
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from datetime import datetime

# ------------------------------
# Configuration
# ------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data/anomalies.csv")

# Load parameters
with open('params.yaml', 'r') as f:
    params = yaml.safe_load(f)

MODEL_CONFIG = params['model']

# MLflow settings
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME", "pothole_kmeans_model")

# Metric thresholds from params
SIL_THRESHOLD = MODEL_CONFIG['silhouette_threshold']
INERTIA_THRESHOLD = MODEL_CONFIG['inertia_threshold']
DATA_DRIFT_THRESHOLD = MODEL_CONFIG['datadrift_threshold']

# ------------------------------
# Setup MLflow
# ------------------------------
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
client = MlflowClient()

class ModelMonitor:
    def __init__(self, metrics_file="model_metrics_history.json"):
        self.metrics_file = metrics_file
        self.history = self.load_history()
    
    def load_history(self):
        """Load historical metrics"""
        if os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_metrics(self, model_version, sil_score, inertia, data_size, timestamp):
        """Save current metrics to history"""
        entry = {
            'timestamp': timestamp,
            'model_version': model_version,
            'silhouette_score': float(sil_score),
            'inertia': float(inertia),
            'data_size': data_size
        }
        
        self.history.append(entry)
        
        with open(self.metrics_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def check_performance_degradation(self, current_sil_score, current_inertia):
        """Check if performance is degrading over time"""
        if len(self.history) < 2:
            return False
        
        # Get recent performance (last 3 entries)
        recent = self.history[-3:]
        avg_sil = np.mean([entry['silhouette_score'] for entry in recent])
        avg_inertia = np.mean([entry['inertia'] for entry in recent])
        
        # Check for significant degradation
        sil_degradation = (avg_sil - current_sil_score) / avg_sil > 0.1
        inertia_degradation = (current_inertia - avg_inertia) / avg_inertia > 0.1
        
        return sil_degradation or inertia_degradation

def load_latest_production_model():
    """Load the latest production model from MLflow"""
    try:
        # Get all model versions
        model_versions = client.search_model_versions(f"name='{MODEL_NAME}'")
        
        if not model_versions:
            print("No models found in registry")
            return None, None, None
        
        # Find production models by checking current_stage
        production_models = [mv for mv in model_versions if mv.current_stage == "Production"]
        
        if production_models:
            # Get latest production model
            latest_prod = sorted(production_models, key=lambda m: int(m.version), reverse=True)[0]
            model_uri = f"models:/{MODEL_NAME}/production"
        else:
            # No production model, use latest model regardless of stage
            print("No production model found, using latest model")
            latest_model = sorted(model_versions, key=lambda m: int(m.version), reverse=True)[0]
            model_uri = f"models:/{MODEL_NAME}/{latest_model.version}"
            latest_prod = latest_model
        
        print(f"Loaded model version {latest_prod.version} (stage: {latest_prod.current_stage})")
        model = mlflow.sklearn.load_model(model_uri)
        
        return model, latest_prod.version, latest_prod.run_id
        
    except Exception as e:
        print(f"Failed to load model: {e}")
        return None, None, None
    
    
def evaluate_model_on_new_data(model, new_data):
    """Evaluate existing model on new data"""
    try:
        # Prepare features (same as training)
        features = new_data[["acc_x", "acc_y", "acc_z", "speed_diff", "magnitude", "road_type"]]
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features.fillna(features.mean()))
        
        # Get predictions
        clusters = model.predict(scaled_features)
        
        # Calculate metrics
        inertia = calculate_inertia(model, scaled_features)
        sil_score = silhouette_score(scaled_features, clusters)
        
        return sil_score, inertia, clusters
        
    except Exception as e:
        print(f"Error evaluating model on new data: {e}")
        return 0, float('inf'), None

def calculate_inertia(model, data):
    """Calculate inertia for KMeans model"""
    try:
        if hasattr(model, 'inertia_'):
            return model.inertia_
        else:
            distances = model.transform(data)
            return np.min(distances, axis=1).sum()
    except Exception as e:
        print(f"Could not calculate inertia: {e}")
        return float('inf')

def check_data_drift(new_data):
    """Simple data drift detection using stored statistics"""
    try:
        # Load or create data stats
        stats_file = "data_statistics.json"
        
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                old_stats = json.load(f)
        else:
            # First time - create initial stats
            old_stats = calculate_data_stats(new_data)
            with open(stats_file, 'w') as f:
                json.dump(old_stats, f, indent=2)
            print("Created initial data statistics")
            return False
        
        # Calculate current stats
        current_stats = calculate_data_stats(new_data)
        
        # Compare mean values for key features
        drift_features = ["acc_x", "acc_y", "acc_z"]
        drift_score = 0
        
        for feature in drift_features:
            old_mean = old_stats[feature]['mean']
            new_mean = current_stats[feature]['mean']
            drift_score += abs(old_mean - new_mean) / (abs(old_mean) + 1e-8)
        
        drift_score /= len(drift_features)
        
        print(f"Data drift score: {drift_score:.4f} (threshold: {DATA_DRIFT_THRESHOLD})")
        
        # Update stats for next time
        with open(stats_file, 'w') as f:
            json.dump(current_stats, f, indent=2)
        
        return drift_score > DATA_DRIFT_THRESHOLD
        
    except Exception as e:
        print(f"Could not calculate data drift: {e}")
        return False

def calculate_data_stats(data):
    """Calculate statistics for data drift detection"""
    stats = {}
    for col in ["acc_x", "acc_y", "acc_z", "speed_diff", "magnitude"]:
        if col in data.columns:
            stats[col] = {
                'mean': float(data[col].mean()),
                'std': float(data[col].std()),
                'min': float(data[col].min()),
                'max': float(data[col].max())
            }
    return stats

def main():
    print("Starting MLOps pipeline evaluation...")
    print(f"Using thresholds - Silhouette: {SIL_THRESHOLD}, Inertia: {INERTIA_THRESHOLD}")
    
    # Load new data
    try:
        new_data = pd.read_csv(DATA_PATH)
        print(f"Loaded new data with {len(new_data)} samples")
    except Exception as e:
        print(f"Failed to load new data: {e}")
        return
    
    # Initialize monitor
    monitor = ModelMonitor()
    
    # Try to load existing production model
    model, model_version, run_id = load_latest_production_model()
    
    if model is None:
        print("No existing model found -> Training new model")
        retrain_model()
        return
    
    # Evaluate existing model on NEW data
    print("Evaluating existing model on new data...")
    sil_score, inertia, clusters = evaluate_model_on_new_data(model, new_data)
    
    print(f"Current Model on New Data -> Silhouette: {sil_score:.4f}, Inertia: {inertia:.4f}")
    
    # Save current metrics
    monitor.save_metrics(
        model_version=model_version,
        sil_score=sil_score,
        inertia=inertia,
        data_size=len(new_data),
        timestamp=datetime.now().isoformat()
    )
    
    # Check if retraining is needed
    retrain_needed = False
    reasons = []
    
    if sil_score < SIL_THRESHOLD:
        retrain_needed = True
        reasons.append(f"Silhouette score ({sil_score:.4f}) below threshold ({SIL_THRESHOLD})")
    
    if inertia > INERTIA_THRESHOLD:
        retrain_needed = True
        reasons.append(f"Inertia ({inertia:.4f}) above threshold ({INERTIA_THRESHOLD})")
    
    # Check for data drift
    if check_data_drift(new_data):
        retrain_needed = True
        reasons.append("Significant data drift detected")
    
    # Check for performance degradation
    if monitor.check_performance_degradation(sil_score, inertia):
        retrain_needed = True
        reasons.append("Performance degradation detected")
    
    # Save evaluation results for DVC
    evaluation_results = {
        'evaluation': {
            'silhouette_score': float(sil_score),
            'inertia': float(inertia),
            'retrain_needed': retrain_needed,
            'reasons': reasons,
            'thresholds': {
                'silhouette': SIL_THRESHOLD,
                'inertia': INERTIA_THRESHOLD
            },
            'timestamp': datetime.now().isoformat()
        }
    }
    
    with open('model_metrics.json', 'w') as f:
        json.dump(evaluation_results, f, indent=2)
    
    if retrain_needed:
        print(f"Retraining needed: {', '.join(reasons)}")
        retrain_model()
    else:
        print("Model performance acceptable -> No retraining needed")

def retrain_model():
    """Trigger model retraining"""
    try:
        print("Starting model retraining...")
        # Set environment variable to handle Unicode in Windows
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            ["python", "app.py"], 
            check=True, 
            capture_output=True, 
            text=True,
            env=env,
            encoding='utf-8'
        )
        print("Retraining completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Retraining failed: {e}")
        print(f"Error output: {e.stderr}")
        # Create empty output file to satisfy DVC
        pd.DataFrame().to_csv('output.csv', index=False)
    except Exception as e:
        print(f"Unexpected error during retraining: {e}")
        # Create empty output file to satisfy DVC
        pd.DataFrame().to_csv('output.csv', index=False)

if __name__ == "__main__":
    main()