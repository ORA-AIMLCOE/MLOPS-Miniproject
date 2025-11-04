import streamlit as st
import pandas as pd
import oracledb
import requests
import os
from datetime import datetime
import tempfile

# -------------------------
# CONFIGURATION
# -------------------------
# Oracle connection details
DB_USER = "MLOPS"
DB_PASSWORD = "thgnf66hm3uDkbYz"
DB_DSN = "sandbox_medium"  # Example: "adb.ap-mumbai-1.oraclecloud.com:1522/yourdbname_high"
WALLET_PATH = "wallet"
TARGET_TABLE = "ANOMALIES"

UPLOAD_DIR = r"C:\Users\Tuttagunta Sowmya\Documents\AIML\MLOPS\my_work\data\new_data"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# Jenkins webhook URL
JENKINS_WEBHOOK_URL = "http://localhost:8080/generic-webhook-trigger/invoke"
JENKINS_URL = "http://localhost:8080/job/CountCSVRows/buildWithParameters"
JENKINS_USER = "sowmya"
JENKINS_TOKEN = "119a799408b7f78ea8ea0a9d77c41f6cc6"
# Table to insert into

# -------------------------
# DATABASE FUNCTIONS
# -------------------------
def get_connection():
    """Create Oracle DB connection"""
    try:
        conn = oracledb.connect(
            config_dir=WALLET_PATH,
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=DB_DSN,
            wallet_location=WALLET_PATH,
            wallet_password=DB_PASSWORD,
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None


# def insert_to_db(df):
#     """Insert a DataFrame into Oracle table"""
#     conn = get_connection()
#     if conn is None:
#         return False

#     cursor = conn.cursor()
#     try:
#         for _, row in df.iterrows():
#             placeholders = ','.join([':' + str(i+1) for i in range(len(row))])
#             sql = f"INSERT INTO {TARGET_TABLE} VALUES ({placeholders})"
#             cursor.execute(sql, tuple(row))
#         conn.commit()
#         cursor.close()
#         conn.close()
#         return True
#     except Exception as e:
#         conn.rollback()
#         st.error(f"Insert failed: {e}")
#         return False


def insert_to_db(df):
    """
    Insert a DataFrame into Oracle table assuming all columns are VARCHAR2.
    
    Args:
        df (pd.DataFrame): Data to insert
    Returns:
        bool: True if insert succeeded, False otherwise
    """
    # -------------------------------
    # 1. Data cleaning
    # -------------------------------
    # Convert all values to string and strip whitespace
    df = df.applymap(lambda x: str(x).strip() if pd.notnull(x) else None)

    # -------------------------------
    # 2. Database insert
    # -------------------------------
    conn = get_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    try:
        for _, row in df.iterrows():
            placeholders = ','.join([':' + str(i+1) for i in range(len(row))])
            sql = f"INSERT INTO {TARGET_TABLE} VALUES ({placeholders})"
            cursor.execute(sql, tuple(row))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Insert failed: {e}")
        return False



def trigger_jenkins(payload):
    """Trigger Jenkins build with parameters"""
    try:
        response = requests.post(
            "http://localhost:8080/job/CountCSVRows/buildWithParameters",
            params={
                "token": "countcsvtoken",
                "file_path": payload.get("file_path", ""),
                "source": payload.get("source", "unknown"),
                "timestamp": payload.get("timestamp", "")
            },
            auth=(JENKINS_USER, JENKINS_TOKEN),
            timeout=15
        )

        if response.status_code == 201:
            st.success("✅ Jenkins pipeline triggered successfully!")
        else:
            st.warning(f"⚠️ Jenkins returned status: {response.status_code}")
    except Exception as e:
        st.error(f"Failed to trigger Jenkins: {e}")



# -------------------------
# STREAMLIT UI
# -------------------------
st.set_page_config(page_title="MLOps Data Ingestion UI", page_icon="📦", layout="wide")
st.title("📦 MLOps Data Ingestion & Pipeline Trigger")
st.write("Insert new data → push to Oracle → trigger Jenkins pipeline")

option = st.radio("Select data input method:", ("Upload CSV", "Manual Entry"))

if option == "Upload CSV":
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file is not None:
        # ✅ Step 3: Best practice — timestamped file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{os.path.splitext(uploaded_file.name)[0]}_{timestamp}.csv"
        saved_path = os.path.join(UPLOAD_DIR, file_name)

        # Save file permanently with timestamp
        with open(saved_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"✅ File saved at: {saved_path}")

        # Load the CSV for DB insertion
        try:
            df = pd.read_csv(saved_path)
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"❌ Failed to read CSV: {e}")
            df = None

        # On button click
        if st.button("🚀 Insert"):
            if df is not None and insert_to_db(df):
                st.success("✅ Data inserted into Oracle DB")
                trigger_jenkins({
                    "source": "upload_csv",
                    "timestamp": str(datetime.now()),
                    "file_path": saved_path,
                    "rows": len(df)
                })

else:
    st.subheader("Enter data manually")
    col1, col2, col3 = st.columns(3)
    with col1:
        id_val = st.text_input("ID")
    with col2:
        name_val = st.text_input("Name")
    with col3:
        score_val = st.number_input("Score", min_value=0.0, max_value=100.0, step=0.1)

    if st.button("🚀 Insert & Trigger Jenkins"):
        data = {"ID": id_val, "Name": name_val, "Score": score_val}
        df = pd.DataFrame([data])
        if insert_to_db(df):
            st.success("✅ Data inserted into Oracle DB")
            trigger_jenkins({
                "source": "manual_entry",
                "timestamp": str(datetime.now()),
                "rows": 1
            })

st.markdown("---")
# st.caption("Built with ❤️ using Streamlit, Oracle, and Jenkins.")