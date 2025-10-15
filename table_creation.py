import oracledb
import pandas as pd
import sys

# ---------- CONFIGURATION ----------
# Update these with your ADB detailsgit status
DB_USER = "MLOPS"
DB_PASSWORD = "thgnf66hm3uDkbYz"
DB_DSN = "sandbox_medium"  # Example: "adb.ap-mumbai-1.oraclecloud.com:1522/yourdbname_high"

CSV_FILE = "anomalies.csv"
TABLE_NAME = "ANOMALIES"
WALLET_PATH = "wallet"
# -----------------------------------


def create_table_if_not_exists(cursor, columns):
    """
    Creates the table dynamically if it doesn't exist, based on CSV headers.
    """
    # Check if table exists
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM user_tables
        WHERE table_name = UPPER('{TABLE_NAME}')
    """)
    exists = cursor.fetchone()[0] > 0

    if exists:
        print(f"✅ Table '{TABLE_NAME}' already exists.")
        return

    # Construct CREATE TABLE statement dynamically
    col_defs = []
    for col in columns:
        col_name = col.upper().replace(" ", "_")
        col_defs.append(f'"{col_name}" VARCHAR2(4000)')
    create_sql = f"CREATE TABLE {TABLE_NAME} ({', '.join(col_defs)})"

    cursor.execute(create_sql)
    print(f"🆕 Table '{TABLE_NAME}' created successfully.")


def insert_data(connection, df):
    """
    Inserts data from DataFrame into the table.
    """
    cursor = connection.cursor()

    # Create table if needed
    create_table_if_not_exists(cursor, df.columns)

    # Prepare insert query
    columns = [col.upper().replace(" ", "_") for col in df.columns]
    placeholders = ", ".join([f":{i+1}" for i in range(len(columns))])
    insert_sql = f"INSERT INTO {TABLE_NAME} ({', '.join(columns)}) VALUES ({placeholders})"

    # Convert DataFrame rows to tuples
    data_tuples = [tuple(map(str, row)) for row in df.to_numpy()]

    # Insert in batches
    cursor.executemany(insert_sql, data_tuples)
    connection.commit()
    print(f"✅ Inserted {len(data_tuples)} rows into '{TABLE_NAME}'.")


def main():
    try:
        # Read the CSV
        df = pd.read_csv(CSV_FILE)
        if df.empty:
            print("⚠️ The CSV file is empty.")
            sys.exit(1)

        print(f"📄 Loaded {len(df)} rows from {CSV_FILE}")

        # Connect to Oracle Autonomous DB
        print("🔌 Connecting to Oracle Autonomous Database...")

        try:
            connection = oracledb.connect(
                config_dir=WALLET_PATH,
                user=DB_USER,
                password=DB_PASSWORD,
                dsn=DB_DSN,
                wallet_location=WALLET_PATH,
                wallet_password=DB_PASSWORD,
            )
        except Exception as e:
            raise Exception('Failed to make the connection', str(e))

        # cursor = connection.cursor()        
        print("✅ Connected successfully.")

        insert_data(connection, df)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        try:
            connection.close()
        except:
            pass


if __name__ == "__main__":
    main()
