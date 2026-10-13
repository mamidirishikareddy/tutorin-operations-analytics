# ui/components/pending_checkout.py

import streamlit as st
import requests
from datetime import datetime, date

BASE_URL = "http://localhost:8000"

def display():
    st.subheader("🕓 Students Still Inside")
    try:
        students_resp = requests.get(f"{BASE_URL}/students/?include_frozen=true")
        students_resp.raise_for_status()
        students = {s["id"]: s for s in students_resp.json()}
    except:
        st.error("❌ Could not fetch students.")
        return

    try:
        attendance_resp = requests.get(f"{BASE_URL}/attendance/all")
        attendance_resp.raise_for_status()
        attendance = attendance_resp.json()
    except:
        st.error("❌ Could not fetch attendance.")
        return

    today_str = str(date.today())

    # Filter: today's records with check-in but no checkout
    still_inside = [
        a for a in attendance
        if a["date"] == today_str and a["checkin_time"] and not a["checkout_time"]
    ]

    if not still_inside:
        st.success("🎉 No students currently inside. All checked out.")
        return

    for record in still_inside:
        student = students.get(record["student_id"], {})
        name = student.get("name", "Unknown")
        class_level = student.get("class_level", "")
        checkin_time = format_time(record.get("checkin_time"))

        duration = "-"
        if record.get("checkin_time"):
            duration = compute_duration_minutes(record["checkin_time"])

        with st.container():
            st.markdown(f"""
                <div style="padding:10px; border-left: 6px solid orange; background-color: #fff7e6;">
                    <b>{name}</b> (Class {class_level})<br>
                    ⏱️ Check-in: {checkin_time} &nbsp;&nbsp; ⏳ Inside for: {duration}
                </div>
            """, unsafe_allow_html=True)

# ----------------------------------------
# Helpers
# ----------------------------------------

def format_time(time_str):
    try:
        dt = datetime.fromisoformat(time_str)
        return dt.strftime("%H:%M")
    except:
        return "-"

def compute_duration_minutes(checkin_str):
    try:
        checkin_time = datetime.fromisoformat(checkin_str)
        now = datetime.now()
        mins = int((now - checkin_time).total_seconds() / 60)
        hrs = mins // 60
        rem = mins % 60
        return f"{hrs:02d}:{rem:02d}"
    except:
        return "-"
