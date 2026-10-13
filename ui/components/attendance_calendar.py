# ui/components/attendance_calendar.py

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import streamlit.components.v1 as components

BASE_URL = "http://localhost:8000"

def display():
    st.subheader("📅 Attendance Overview")

    # -----------------------------
    # JS Calendar Input (HTML + JS injection)
    # -----------------------------
    selected_date = st.session_state.get("selected_date", date.today())
    st.markdown("#### 📆 Select a Date")

    calendar_html = f"""
    <input type="date" id="calendar" name="calendar" value="{selected_date}" style="font-size:18px; padding:5px; width:50%; border-radius: 6px;">
    <script>
    const calendar = document.getElementById("calendar");
    calendar.addEventListener("change", function() {{
        const date = calendar.value;
        const streamlitInput = window.parent.document.querySelector('input[data-testid="stTextInput"]');
        if (streamlitInput) {{
            streamlitInput.value = date;
            streamlitInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
        }}
    }});
    </script>
    """
    components.html(calendar_html, height=60)

    selected_date_str = st.text_input("Selected Date", str(selected_date), label_visibility="collapsed")
    try:
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    except ValueError:
        selected_date = date.today()

    # -----------------------------
    # Fetch Students
    # -----------------------------
    with st.spinner("Loading student data..."):
        try:
            students_resp = requests.get(f"{BASE_URL}/students/?include_frozen=true")
            students_resp.raise_for_status()
            students = students_resp.json()
        except Exception:
            st.error("❌ Failed to load student data.")
            return

    student_dict = {s["id"]: s for s in students}
    total_students = len([s for s in students if s.get("is_active", True)])

    # -----------------------------
    # Fetch All Attendance Records
    # -----------------------------
    with st.spinner("Loading attendance records..."):
        try:
            attendance_resp = requests.get(f"{BASE_URL}/attendance/all")
            attendance_resp.raise_for_status()
            all_attendance = attendance_resp.json()
        except Exception:
            st.error("❌ Failed to load attendance records.")
            return

    # -----------------------------
    # Filter Attendance for Selected Date
    # -----------------------------
    selected_str = str(selected_date)
    present_today = [a for a in all_attendance if a["date"] == selected_str]
    present_ids = {a["student_id"] for a in present_today}

    active_students = [s for s in students if s.get("is_active", True) and not s.get("is_frozen", False)]
    absent_students = [s for s in active_students if s["id"] not in present_ids]
    new_joins = [s for s in active_students if s.get("joining_date") == selected_str]

    # -----------------------------
    # Summary Metrics
    # -----------------------------
    st.markdown("### 📊 Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("👨‍🎓 Total Students", total_students)
    col2.metric("🟢 Present", len(present_today))
    col3.metric("❌ Absent", len(absent_students))

    # -----------------------------
    # New Joiners Section
    # -----------------------------
    with st.expander("🆕 New Admissions on Selected Date"):
        if new_joins:
            for s in new_joins:
                st.markdown(f"👋 **{s['name']}** (Class `{s['class_level']}`)", unsafe_allow_html=True)
        else:
            st.info("No new admissions on this date.")

    # -----------------------------
    # Absentees Section
    # -----------------------------
    with st.expander("❌ Absent Students"):
        if absent_students:
            for s in absent_students:
                st.markdown(f"• {s['name']} (Class `{s['class_level']}`)", unsafe_allow_html=True)
        else:
            st.success("🎉 Everyone was present!")

    # -----------------------------
    # Present Students Section
    # -----------------------------
    with st.expander("🟢 Present Students (with Timings)"):
        if present_today:
            df = pd.DataFrame([{
                "Student": student_dict.get(p["student_id"], {}).get("name", "Unknown"),
                "Class": student_dict.get(p["student_id"], {}).get("class_level", "-"),
                "Check-in": format_time(p.get("checkin_time")),
                "Check-out": format_time(p.get("checkout_time")),
                "Duration": format_duration(p.get("duration_minutes"))
            } for p in present_today])
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No students marked present on this date.")

    # -----------------------------
    # Class-wise Breakdown
    # -----------------------------
    if st.toggle("📊 Show Class-wise Attendance Breakdown"):
        df_all = pd.DataFrame(active_students)
        df_all["present"] = df_all["id"].apply(lambda x: 1 if x in present_ids else 0)
        summary = df_all.groupby("class_level").agg(
            Total=("id", "count"),
            Present=("present", "sum")
        )
        summary["Absent"] = summary["Total"] - summary["Present"]
        st.dataframe(summary.reset_index(), use_container_width=True)

# -----------------------------
# Utility Functions
# -----------------------------
def format_time(time_str):
    if not time_str:
        return "-"
    try:
        dt = datetime.fromisoformat(time_str)
        return dt.strftime("%H:%M")
    except Exception:
        return time_str

def format_duration(minutes):
    if minutes is None:
        return "-"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"
