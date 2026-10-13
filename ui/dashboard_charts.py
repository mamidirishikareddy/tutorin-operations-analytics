import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from app.db import get_session
from app.models import Student, ToDoItem, Attendance
from sqlalchemy import func, cast, Date

# ------------------------------
# Tile Renderer
# ------------------------------
def metric_tile(icon, label, value, color="#ffffff", bgcolor="#4a4a4a"):
    st.markdown(f"""
        <div style="background:{bgcolor}; padding:1rem; border-radius:10px;
                    text-align:center; color:{color}; transition:0.3s ease;"
             onmouseover="this.style.transform='scale(1.02)'"
             onmouseout="this.style.transform='scale(1)'">
            <div style="font-size:2rem;">{icon} {value}</div>
            <div style="font-size:0.9rem; color:lightgray;">{label}</div>
        </div>
    """, unsafe_allow_html=True)

# ------------------------------
# Dashboard Main View
# ------------------------------
def show_dashboard():
    st.subheader("📊 Overview Dashboard")

    session = get_session()
    try:
        # ---------------------------
        # Live Header
        # ---------------------------
        st.markdown(f"""
            <div style="display:flex;justify-content:space-between;margin-bottom:1rem;">
                <h3>👋 Welcome, {st.session_state.get('name', 'User')}</h3>
                <div style="text-align:right;font-weight:normal;">
                    <span style="color:gray;">📅 {datetime.now().strftime('%A, %d %B %Y')}<br>⏰ {datetime.now().strftime('%I:%M:%S %p')}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # ---------------------------
        # Metrics Summary
        # ---------------------------
        total_students = session.query(func.count(Student.id)).scalar() or 0
        present_today = session.query(func.count(Attendance.id)).filter(
            cast(Attendance.date, Date) == datetime.now().date()
        ).scalar() or 0
        total_tasks = session.query(func.count(ToDoItem.id)).scalar() or 0
        completed_tasks = session.query(func.count(ToDoItem.id)).filter(ToDoItem.is_done == True).scalar() or 0
        pending_tasks = total_tasks - completed_tasks

        st.markdown("### 📌 Quick Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            metric_tile("👨‍🎓", "Total Students", total_students, bgcolor="#2E86AB")
        with col2:
            metric_tile("🟢", "Present Today", present_today, bgcolor="#28B463")
        with col3:
            metric_tile("📝", "Pending Tasks", pending_tasks, bgcolor="#E67E22")

        # ---------------------------
        # Schedule Block
        # ---------------------------
        st.markdown("### 📅 Today's Schedule")
        st.info("""
        • 10:00 AM – Class 10 Maths  
        • 12:00 PM – Class 9 Science  
        • 05:00 PM – Homework Review
        """)

        # ---------------------------
        # Attendance Trends
        # ---------------------------
        st.markdown("### 📈 Attendance Trend (Last 7 Days)")
        last_7_days = [(datetime.now().date() - timedelta(days=i)) for i in range(6, -1, -1)]
        attendance_counts = []

        for day in last_7_days:
            count = session.query(func.count(Attendance.id)).filter(
                cast(Attendance.date, Date) == day
            ).scalar() or 0
            attendance_counts.append({"Date": day.strftime("%d %b"), "Count": count})

        attendance_df = pd.DataFrame(attendance_counts)

        attendance_chart = alt.Chart(attendance_df).mark_line(
            point=alt.OverlayMarkDef(filled=True, fill="white")
        ).encode(
            x=alt.X("Date", title="Date"),
            y=alt.Y("Count", title="Present Students"),
            tooltip=["Date", "Count"]
        ).properties(height=300).interactive()

        st.altair_chart(attendance_chart, use_container_width=True)

        # ---------------------------
        # To-Do Pie Chart
        # ---------------------------
        st.markdown("### ✅ To-Do Completion Status")
        if total_tasks == 0:
            st.info("No to-do tasks available.")
        else:
            todo_df = pd.DataFrame({
                "Status": ["Completed", "Pending"],
                "Count": [completed_tasks, pending_tasks]
            })

            todo_chart = alt.Chart(todo_df).mark_arc(innerRadius=50).encode(
                theta="Count",
                color=alt.Color("Status", scale=alt.Scale(range=["#2E7D32", "#FFC107"])),
                tooltip=["Status", "Count"]
            ).properties(width=350, height=350)

            st.altair_chart(todo_chart, use_container_width=False)

        # ---------------------------
        # Quick Links to Other Tabs
        # ---------------------------
        st.markdown("### 🔗 Quick Links")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("👨‍🎓 Students"):
                st.session_state.current_page = "👨‍🎓 Students"
                st.rerun()
        with col2:
            if st.button("🕘 Attendance"):
                st.session_state.current_page = "🕘 Attendance"
                st.rerun()
        with col3:
            if st.button("🧪 Test Scores"):
                st.session_state.current_page = "🧪 Test Scores"
                st.rerun()
        with col4:
            if st.button("💰 Fees"):
                st.session_state.current_page = "💰 Fees"
                st.rerun()

        # ---------------------------
        # Quote Block
        # ---------------------------
        st.markdown("### 💬 Tip of the Day")
        st.success("“Success is the sum of small efforts, repeated day-in and day-out.”")

    finally:
        session.close()
