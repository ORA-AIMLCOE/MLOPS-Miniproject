
import sys
import pandas as pd
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset


def detect_data_drift(baseline_path, new_data_path, html_report_path):
    """
    Detects data drift between baseline and new data using Evidently.
    Generates an HTML report.
    """
    try:
        print("Loading datasets...")
        # Load the two CSV files into pandas DataFrames
        baseline_df = pd.read_csv(baseline_path)
        current_df = pd.read_csv(new_data_path)
        print("✅ Datasets loaded successfully.")

    except FileNotFoundError as e:
        print(f"❌ Error: {e}. Please check the file paths.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred while loading data: {e}")
        sys.exit(1)

    print("Generating data drift report...")
    # Create an Evidently Report with the DataDriftPreset
    data_drift_report = Report(metrics=[
        DataDriftPreset(),
    ])

    # Run the report, comparing the baseline and current data
    data_drift_report.run(
        reference_data=baseline_df,
        current_data=current_df,
        column_mapping=None
    )

    # Save the report to an interactive HTML file
    data_drift_report.save_html(html_report_path)
    print(f"✅ Data drift report saved to: {html_report_path}")

    # --- Corrected logic for accessing the report summary ---
    try:
        report_dict = data_drift_report.as_dict()
        # print("Analyzing report summary...")
        # print(report_dict)  # Debug: Print the entire report dictionary structure
        
        # Access the summary directly from 'metrics.result'
        dataset_drift_detected = report_dict['metrics'][0]['result']['dataset_drift']
        share_drifted_features = report_dict['metrics'][0]['result']['share_of_drifted_columns']

        if dataset_drift_detected:
            print(f"⚠️  Data drift detected! The overall dataset has drifted.")
            print(f"📊 {share_drifted_features:.2%} of features have drifted.")
        else:
            print("✅ No significant data drift detected.")
        data_drift_report.save_json("json_report.json")

    except (KeyError, IndexError) as e:
        print(f"❌ Error accessing report summary: {e}")
        print("The structure of the Evidently report dictionary may have changed.")
        dataset_drift_detected = False

    return dataset_drift_detected



if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python drift_detector.py <baseline_csv> <new_data_csv> <output_report.html>")
        sys.exit(1)

    baseline_file = sys.argv[1]
    new_data_file = sys.argv[2]
    output_html = sys.argv[3]

    # Run the drift detection process
    detect_data_drift(baseline_file, new_data_file, output_html)

