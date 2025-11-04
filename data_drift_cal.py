import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset


# import pandas as pd
# from sklearn import datasets

# from evidently import Report
# from evidently.presets import DataDriftPreset

# iris_data = datasets.load_iris(as_frame=True)
# iris_frame = iris_data.frame

# Load your CSV file
csv_file = "anomalies.csv"  # replace with your CSV file path
df = pd.read_csv(csv_file)

# Optional: split your dataset into reference and current sets
# For example, first 50% as reference, remaining 50% as current
reference_data = df.sample(frac=0.5, random_state=42)
current_data = df.drop(reference_data.index).sample(frac=1.0, random_state=24)

# Create a data drift report
report = Report(
    presets=[DataDriftPreset(method="psi")],
    include_tests=True
)

# Run the report
my_eval = report.run(reference_data, current_data)

# Save the report as HTML
my_eval.save_html("data_drift_report.html")

print("Data drift report generated: data_drift_report.html")
