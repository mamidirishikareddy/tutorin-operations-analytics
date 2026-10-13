# ui/components/audit_viewer.py

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from pytz import timezone

BASE_URL = "http://localhost:8000"

def display():
    st.subheader("📝 Audit Log Viewer")

    # -----------------------------
    # Fetch Logs
    # -----------------------------
    try:
        resp = requests.get(f"{BASE_URL}/audit/")
        resp.raise_for_status()
        logs = resp.json()
    except requests.RequestException as e:
        st.error(f"❌ Failed to load audit logs.\n\n{e}")
        return

    if not logs:
        st.info("ℹ️ No audit logs recorded yet.")
        return

    # -----------------------------
    # Convert timestamps to IST
    # -----------------------------
    ist = timezone("Asia/Kolkata")
    for log in logs:
        try:
            if "timestamp" in log:
                utc_dt = datetime.fromisoformat(log["timestamp"])
                local_dt = utc_dt.astimezone(ist)
                log["timestamp"] = local_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass  # leave as is if error

    # -----------------------------
    # Convert to DataFrame
    # -----------------------------
    df = pd.DataFrame(logs)

    # Ensure required columns exist
    if "timestamp" not in df.columns or "action" not in df.columns or "details" not in df.columns:
        st.error("⚠️ Audit log format is incorrect. Required fields: 'timestamp', 'action', 'details'")
        return

    # -----------------------------
    # Filters
    # -----------------------------
    with st.expander("🔍 Filter Logs"):
        action_options = sorted(df["action"].dropna().unique())
        selected_action = st.selectbox("Action Type", ["All"] + action_options)
        search_text = st.text_input("Search in Details")

    filtered_df = df.copy()
    if selected_action != "All":
        filtered_df = filtered_df[filtered_df["action"] == selected_action]
    if search_text.strip():
        filtered_df = filtered_df[filtered_df["details"].str.contains(search_text, case=False, na=False)]

    # -----------------------------
    # Display Logs
    # -----------------------------
    if filtered_df.empty:
        st.warning("📭 No logs match your filter criteria.")
        return

    for _, row in filtered_df.iterrows():
        timestamp = row.get("timestamp", "N/A")
        action = row.get("action", "Unknown Action")
        details = row.get("details", "No details provided")

        st.markdown(f"""
        <div style="border-left: 4px solid #0d6efd; padding-left: 1rem; margin-bottom: 1rem; background-color: #f9f9f9;">
            <div style="font-size: 13px; color: #555;"><strong>🕒 {timestamp}</strong></div>
            <div style="font-size: 14px;"><strong>Action:</strong> <code>{action}</code></div>
            <div style="font-size: 14px;"><strong>Details:</strong> {details}</div>
        </div>
        """, unsafe_allow_html=True)
