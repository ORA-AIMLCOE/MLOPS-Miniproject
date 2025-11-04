import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# -------------------------
# CONFIGURATION
# -------------------------
BACKEND_BASE_URL = "http://localhost:5001"  # FastAPI backend URL
UPLOAD_ENDPOINT = f"{BACKEND_BASE_URL}/upload_csv/"
MANUAL_ENDPOINT = f"{BACKEND_BASE_URL}/manual_insert/"
HEALTH_ENDPOINT = f"{BACKEND_BASE_URL}/health"
LATEST_ENDPOINT = f"{BACKEND_BASE_URL}/latest"   # 👈 New endpoint to fetch Jenkins messages

# -------------------------
# STREAMLIT UI CONFIG
# -------------------------
st.set_page_config(page_title="📦 MLOps Data Ingestion", page_icon="🔗", layout="wide")
st.title("📦 MLOps Data Ingestion & Pipeline Trigger")
st.caption("Upload data → backend inserts into Oracle DB → triggers Jenkins pipeline")

# -------------------------
# HEALTH CHECK
# -------------------------
try:
    health = requests.get(HEALTH_ENDPOINT, timeout=5)
    if health.status_code == 200:
        st.success("✅ Backend server is online")
    else:
        st.warning("⚠️ Backend not responding correctly")
except Exception as e:
    st.error(f"❌ Cannot reach backend: {e}")

st.markdown("---")

# -------------------------
# FILE UPLOAD SECTION
# -------------------------
option = st.radio("Select data input method:", ("Upload CSV", "Manual Entry"))

if option == "Upload CSV":
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    if uploaded_file is not None:
        # Show a preview
        try:
            df = pd.read_csv(uploaded_file)
            st.write("✅ Preview of uploaded CSV:")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"❌ Failed to read CSV: {e}")
            df = None

        if st.button("🚀 Insert & Trigger Jenkins"):
            try:
                with st.spinner("Uploading and triggering backend..."):
                    response = requests.post(
                        UPLOAD_ENDPOINT,
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")},
                        timeout=60
                    )

                if response.status_code == 200:
                    data = response.json()
                    st.success(f"✅ {data.get('message')}")
                    st.write(f"📂 File Path: {data.get('file_path')}")
                    st.write(f"📊 Rows Inserted: {data.get('rows')}")
                else:
                    st.error(f"❌ Backend error: {response.json().get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"❌ Failed to connect to backend: {e}")

else:
    # -------------------------
    # MANUAL ENTRY SECTION
    # -------------------------
    st.subheader("Enter a single record manually")

    with st.form("manual_entry_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            id_val = st.text_input("ID")
        with col2:
            name_val = st.text_input("Name")
        with col3:
            score_val = st.number_input("Score", min_value=0.0, max_value=100.0, step=0.1)

        submitted = st.form_submit_button("🚀 Trigger Jenkins")

        if submitted:
            if not id_val or not name_val:
                st.warning("Please fill in all fields.")
            else:
                try:
                    with st.spinner("Sending data to backend..."):
                        response = requests.post(
                            MANUAL_ENDPOINT,
                            data={
                                "id_val": id_val,
                                "name_val": name_val,
                                "score_val": score_val
                            },
                            timeout=30
                        )

                    if response.status_code == 200:
                        st.success(response.json().get("message"))
                    else:
                        st.error(f"❌ Backend error: {response.json().get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Failed to connect to backend: {e}")

st.markdown("---")

# -------------------------
# LIVE BACKEND MESSAGE MONITOR
# -------------------------
st.subheader("📡 Live Jenkins / Backend Messages")
placeholder = st.empty()

# Poll /latest endpoint every few seconds
poll_interval = 3 # seconds
last_message = None

while True:
    try:
        response = requests.get(LATEST_ENDPOINT, timeout=5)
        if response.status_code == 200:
            data = response.json()
            msg = data.get("message", "")
            if msg and msg != last_message:
                placeholder.success(f"📢 {datetime.now().strftime('%H:%M:%S')} — {msg}")
                last_message = msg
            elif not msg:
                placeholder.info("Waiting for Jenkins to send a message...")
        else:
            placeholder.info("Jenkins is running. Hold tight!")
    except Exception as e:
        placeholder.error(f"❌ Error while polling backend: {e}")

    time.sleep(poll_interval)
