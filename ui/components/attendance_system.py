# ui/components/attendance_system.py

import streamlit as st
from datetime import datetime, date, time
import requests

API = "http://localhost:8000/attendance"

def render_attendance_ui(student):
    st.markdown("## 🕘 Attendance Tracker")

    today = date.today()
    now = datetime.now().replace(microsecond=0)

    # Fetch today's attendance for the student
    student_attendance = requests.get(f"{API}/student/{student.id}").json()
    today_attendance = next((a for a in student_attendance if a["date"] == today.isoformat()), None)

    # -------------------------------
    # Real-time Check-in/out Section
    # -------------------------------
    st.subheader("🔴 Real-Time Attendance")
    col1, col2 = st.columns(2)

    with col1:
        if not today_attendance or today_attendance["checkin_time"] is None:
            if st.button("✅ Check-In Now"):
                payload = {
                    "student_id": student.id,
                    "checkin_time": now.isoformat()
                }
                res = requests.post(f"{API}/mark", json=payload)
                if res.status_code == 200:
                    st.success("✅ Check-in recorded.")
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "Error"))
        else:
            st.info(f"🟢 Checked-in: `{today_attendance['checkin_time'][11:16]}`")

    with col2:
        if today_attendance and today_attendance["checkin_time"] and today_attendance["checkout_time"] is None:
            if st.button("🚪 Check-Out Now"):
                payload = {
                    "student_id": student.id,
                    "checkout_time": now.isoformat()
                }
                res = requests.post(f"{API}/checkout", json=payload)
                if res.status_code == 200:
                    st.success("✅ Checked out successfully.")
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "Error"))
        elif today_attendance and today_attendance["checkout_time"]:
            st.info(f"🔚 Checked-out: `{today_attendance['checkout_time'][11:16]}`")

    # -------------------------------
    # Manual Entry
    # -------------------------------
    st.markdown("---")
    st.subheader("✍️ Manual Attendance Entry (Today or Past)")
    with st.form("manual_entry"):
        manual_date = st.date_input("Date", value=today, max_value=today)
        checkin = st.time_input("Check-In Time", value=time(9, 0))
        checkout = st.time_input("Check-Out Time", value=time(12, 0))

        submit = st.form_submit_button("📌 Submit Manual Entry")
        if submit:
            if checkout <= checkin:
                st.warning("Check-out must be after check-in.")
            else:
                duration = int((datetime.combine(today, checkout) - datetime.combine(today, checkin)).total_seconds() // 60)
                payload = {
                    "student_id": student.id,
                    "checkin_time": datetime.combine(manual_date, checkin).isoformat(),
                    "checkout_time": datetime.combine(manual_date, checkout).isoformat(),
                    "duration_minutes": duration,
                    "date": manual_date.isoformat()
                }
                # Create a dummy attendance object (only for admin/manual edits)
                res = requests.put(f"{API}/edit/0", json=payload)  # change this route for admin
                st.success("✅ Manual attendance saved (dev mode).")
                st.rerun()

    # -------------------------------
    # Attendance Summary
    # -------------------------------
    st.markdown("---")
    st.subheader("📊 Attendance Summary")
    summary = requests.get(f"{API}/summary/{student.id}").json()
    st.write(f"✅ **Total Present Days:** {summary['total_present']}")
    st.write(f"⏱️ **Average Duration:** {summary['avg_duration']} minutes")

    # -------------------------------
    # Today’s Status Indicator
    # -------------------------------
    st.markdown("---")
    st.subheader("📅 Today's Status")

    if not today_attendance:
        st.warning("❌ No check-in today.")
    elif today_attendance["checkout_time"]:
        st.success("🟢 Completed for today.")
    else:
        st.info("🕓 Still inside. Not checked out yet.")

