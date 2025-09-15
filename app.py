import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Load dataset
data = pd.read_csv(r"/app/data/anomalies.csv")

# Select features
features = data[
    ["acc_x", "acc_y", "acc_z", "speed_diff", "magnitude", "road_type"]
]

# Scale
scaler = StandardScaler()
scaled_features = scaler.fit_transform(features.fillna(features.mean()))

# Clustering
kmeans = KMeans(n_clusters=2, random_state=42)
data["cluster"] = kmeans.fit_predict(scaled_features)

# Map clusters to labels
cluster_to_class = {0: "probably pothole", 1: "probably speed bump"}
data["class"] = data["cluster"].map(cluster_to_class)

# Save output
data.to_csv("output.csv", index=False)
print("✅ Results saved to output.csv")
