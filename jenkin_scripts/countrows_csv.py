import pandas as pd
import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: python count_rows.py <path_to_csv>")
        sys.exit(1)

    csv_path = sys.argv[1]

    if not os.path.exists(csv_path):
        print(f"Error: File not found at {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    print(f"✅ File '{csv_path}' has {len(df)} rows.")

if __name__ == "__main__":
    main()
