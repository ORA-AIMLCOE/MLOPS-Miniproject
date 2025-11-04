from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.responses import JSONResponse
import pandas as pd
import oracledb
import requests
import os
from datetime import datetime
import tempfile

# -------------------------------
# CONFIGURATION
# -------------------------------
DB_USER = "MLOPS"
DB_PASSWORD = "thgnf66hm3uDkbYz"
DB_DSN = "sandbox_medium"
WALLET_PATH = "wallet"
TARGET_TABLE = "ANOMALIES"

JENKINS_URL = "http://localhost:8080/job/CountCSVRows/buildWithParameters"
JENKINS_USER = "sowmya"
JENKINS_TOKEN = "119a799408b7f78ea8ea0a9d77c41f6cc6"

UPLOAD_DIR = r"C:\Users\Tuttagunta Sowmya\Documents\AIML\MLOPS\my_work\data\new_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="MLOps Backend API", version="1.0")


# -------------------------------
# DATABASE UTILS
# -------------------------------
def get_connection():
    """Create Oracle DB connection."""
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
        raise Exception(f"Database connection failed: {e}")


def insert_to_db(df: pd.DataFrame) -> bool:
    """Insert a DataFrame into Oracle table."""
    df = df.applymap(lambda x: str(x).strip() if pd.notnull(x) else None)
    conn = get_connection()
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
        cursor.close()
        conn.close()
        raise Exception(f"Insert failed: {e}")


def trigger_jenkins(file_path: str, source: str, rows: int):
    """Trigger Jenkins build with parameters."""
    try:
        response = requests.post(
            JENKINS_URL,
            params={
                "token": "countcsvtoken",
                "file_path": file_path,
                "source": source,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "rows": rows
            },
            auth=(JENKINS_USER, JENKINS_TOKEN),
            timeout=20
        )

        if response.status_code != 201:
            raise Exception(f"Jenkins returned status {response.status_code}")
    except Exception as e:
        raise Exception(f"Failed to trigger Jenkins: {e}")


# -------------------------------
# API ENDPOINTS
# -------------------------------
@app.post("/upload_csv/")
async def upload_csv(file: UploadFile):
    """Handle CSV upload, insert to DB, and trigger Jenkins."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{os.path.splitext(file.filename)[0]}_{timestamp}.csv"
        saved_path = os.path.join(UPLOAD_DIR, filename)

        # Save uploaded file
        with open(saved_path, "wb") as f:
            f.write(await file.read())

        # Read CSV into DataFrame
        df = pd.read_csv(saved_path)
        rows = len(df)

        # Insert into DB
        insert_to_db(df)

        # Trigger Jenkins
        trigger_jenkins(saved_path, "upload_csv", rows)

        return JSONResponse(
            status_code=200,
            content={
                "message": "✅ File inserted and Jenkins triggered successfully",
                "file_path": saved_path,
                "rows": rows,
            },
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

latest_message = {"message": ""}

@app.post("/test")
async def test_endpoint(request: Request):
    data = await request.json()
    msg = data.get("message", "Hello from backend!")
    print("✅ Jenkins payload received:", msg)
    latest_message["message"] = msg
    return {"status": "ok", "received": msg}

@app.get("/latest")
def get_latest_message():
    return latest_message


@app.post("/manual_insert/")
async def manual_insert(id_val: str = Form(...), name_val: str = Form(...), score_val: float = Form(...)):
    """Handle manual entry insertion."""
    try:
        df = pd.DataFrame([{"ID": id_val, "Name": name_val, "Score": score_val}])
        insert_to_db(df)
        trigger_jenkins("manual_entry", "manual_entry", 1)

        return JSONResponse(
            status_code=200,
            content={"message": "✅ Manual data inserted and Jenkins triggered"},
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
