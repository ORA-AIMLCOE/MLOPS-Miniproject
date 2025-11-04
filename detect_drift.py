import sys
import pandas as pd
import json
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset


def detect_data_drift(baseline_path, new_data_path, html_report_path, json_report_path="drift_summary.json"):
    """
    Detects data drift between baseline and new data using Evidently.
    Generates both HTML and JSON summaries.
    """
    print("🔍 Starting drift detection...")
    print(f"Baseline: {baseline_path}")
    print(f"New data: {new_data_path}")

    # 1️⃣ Load datasets
    try:
        baseline_df = pd.read_csv(baseline_path)
        current_df = pd.read_csv(new_data_path)
        print(f"✅ Loaded baseline ({baseline_df.shape}) and new data ({current_df.shape})")
    except Exception as e:
        print(f"❌ Failed to read input CSVs: {e}")
        sys.exit(1)

    # 2️⃣ Generate Evidently report
    try:
        report = Report(metrics=[DataDriftPreset()])
        report.run(reference_data=baseline_df, current_data=current_df)
        report.save_html(html_report_path)
        print(f"📄 HTML drift report saved at: {html_report_path}")
    except Exception as e:
        print(f"❌ Failed to generate Evidently HTML report: {e}")
        sys.exit(1)

    # 3️⃣ Extract drift summary
    try:
        report_dict = report.as_dict()
        result = report_dict["metrics"][0]["result"]
        dataset_drift = result.get("dataset_drift", False)
        drift_share = result.get("share_of_drifted_columns", 0.0)

        summary = {
            "dataset_drift": dataset_drift,
            "share_of_drifted_columns": drift_share,
            "n_columns": result.get("number_of_columns", None),
            "threshold": result.get("dataset_drift_threshold", None),
        }

        with open(json_report_path, "w") as f:
            json.dump(summary, f, indent=4)

        print(f"🧾 JSON summary saved at: {json_report_path}")
        print(f"✅ Drift detected: {dataset_drift} | {drift_share:.2%} of features drifted")

    except Exception as e:
        print(f"❌ Error parsing Evidently results: {e}")
        sys.exit(1)

    # 4️⃣ Exit code for Jenkins
    if dataset_drift:
        print("⚠️ Data drift detected.")
        sys.exit(2)
    else:
        print("✅ No significant data drift detected.")
        sys.exit(0)


if __name__ == "__main__":
    # if len(sys.argv) != 4 and len(sys.argv) != 5:
    #     print("Usage: python detect_drift.py <baseline_csv> <new_data_csv> <output_html> [output_json]")
    #     sys.exit(1)

    baseline_file = r'C:\Users\Tuttagunta Sowmya\Documents\AIML\MLOPS\my_work\anomalies.csv'
    new_data_file = r'C:\Users\Tuttagunta Sowmya\Documents\AIML\MLOPS\my_work\data\new_data\test_anomalies_20251021_153259.csv'
    output_html = r'C:\Users\Tuttagunta Sowmya\Documents\AIML\MLOPS\my_work\data_drift_report.html'
    output_json = r'C:\Users\Tuttagunta Sowmya\Documents\AIML\MLOPS\my_work\json_report.json'
    # output_json = sys.argv[4] if len(sys.argv) == 5 else "drift_summary.json"

    detect_data_drift(baseline_file, new_data_file, output_html, output_json)
