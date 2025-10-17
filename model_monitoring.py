# model_monitoring.py
import pandas as pd
import json
from datetime import datetime
import os

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
            'silhouette_score': sil_score,
            'inertia': inertia,
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