# ui/components/attendance_export.py

import streamlit as st
import pandas as pd
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, extract
from app.db import get_db
from app.models import Attendance, Student


def export_all_attendance():
    db: Session = next(get_db())

    st.subheader("📥 Attendance CSV Export")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🧍 Per Student",
        "🗓 Monthly Export",
        "📆 Date Range Export",
        "📄 All Records"
    ])

    # -------------------------------
    # 1. PER-STUDENT EXPORT
    # -------------------------------
    with tab1:
        students = db.query(Student).order_by(Student.name).all()
        student_options = {f"{s.name} (ID: {s.id})": s.id for s in students}
        selected_label = st.selectbox("Select a student:", list(student_options.keys()))

        if selected_label:
            selected_id = student_options[selected_label]
            records = db.query(Attendance).filter(Attendance.student_id == selected_id).order_by(Attendance.date).all()

            if not records:
                st.warning("No records found for this student.")
            else:
                df = pd.DataFrame([{
                    "Date": r.date.strftime("%Y-%m-%d"),
                    "Check-in": r.checkin_time.strftime("%H:%M") if r.checkin_time else "",
                    "Check-out": r.checkout_time.strftime("%H:%M") if r.checkout_time else "",
                    "Duration (mins)": r.duration_minutes
                } for r in records])

                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv,
                    file_name=f"attendance_student_{selected_id}.csv",
                    mime="text/csv"
                )

    # -------------------------------
    # 2. MONTHLY EXPORT
    # -------------------------------
    with tab2:
        today = date.today()
        selected_month = st.selectbox("Month", list(range(1, 13)), index=today.month - 1)
        selected_year = st.selectbox("Year", list(range(2023, today.year + 1)), index=1)

        records = db.query(Attendance).join(Student).filter(
            extract('year', Attendance.date) == selected_year,
            extract('month', Attendance.date) == selected_month
        ).order_by(Attendance.date, Attendance.student_id).all()

        if not records:
            st.info("No records found for selected month.")
        else:
            df = pd.DataFrame([{
                "Date": r.date.strftime("%Y-%m-%d"),
                "Student ID": r.student_id,
                "Student Name": r.student.name,
                "Class": r.student.class_level,
                "Check-in": r.checkin_time.strftime("%H:%M") if r.checkin_time else "",
                "Check-out": r.checkout_time.strftime("%H:%M") if r.checkout_time else "",
                "Duration (mins)": r.duration_minutes
            } for r in records])

            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Monthly CSV",
                data=csv,
                file_name=f"attendance_{selected_year}_{selected_month:02}.csv",
                mime="text/csv"
            )

    # -------------------------------
    # 3. DATE RANGE EXPORT
    # -------------------------------
    with tab3:
        st.markdown("### 📆 Export by Date Range")
        col1, col2 = st.columns(2)
        start_date = col1.date_input("Start Date", value=date.today().replace(day=1))
        end_date = col2.date_input("End Date", value=date.today())

        students = db.query(Student).order_by(Student.name).all()
        student_filter = st.selectbox("Optional: Filter by Student", ["All"] + [f"{s.name} (ID: {s.id})" for s in students])

        query = db.query(Attendance).join(Student).filter(
            Attendance.date >= start_date,
            Attendance.date <= end_date
        )

        if student_filter != "All":
            student_id = int(student_filter.split("(ID: ")[1].rstrip(")"))
            query = query.filter(Attendance.student_id == student_id)

        records = query.order_by(Attendance.date, Attendance.student_id).all()

        if not records:
            st.warning("No attendance found in this range.")
        else:
            df = pd.DataFrame([{
                "Date": r.date.strftime("%Y-%m-%d"),
                "Student ID": r.student_id,
                "Student Name": r.student.name,
                "Class": r.student.class_level,
                "Check-in": r.checkin_time.strftime("%H:%M") if r.checkin_time else "",
                "Check-out": r.checkout_time.strftime("%H:%M") if r.checkout_time else "",
                "Duration (mins)": r.duration_minutes
            } for r in records])

            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"attendance_{start_date}_to_{end_date}.csv",
                mime="text/csv"
            )

    # -------------------------------
    # 4. EXPORT ALL ATTENDANCE
    # -------------------------------
    with tab4:
        st.markdown("### 📄 Full Attendance Record (All Students, All Dates)")

        result = db.execute(
            select(
                Attendance.id,
                Attendance.date,
                Attendance.checkin_time,
                Attendance.checkout_time,
                Attendance.duration_minutes,
                Student.name,
                Student.class_level,
                Student.id.label("student_id")
            ).join(Student, Attendance.student_id == Student.id)
        ).fetchall()

        if not result:
            st.warning("⚠️ No attendance records found.")
            return

        df = pd.DataFrame(result)
        df = df.rename(columns={
            "id": "Record ID",
            "student_id": "Student ID",
            "name": "Student Name",
            "class_level": "Class",
            "date": "Date",
            "checkin_time": "Check-In",
            "checkout_time": "Check-Out",
            "duration_minutes": "Duration (mins)"
        })

        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        filename = f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        st.download_button(
            label="⬇️ Download All Records CSV",
            data=csv,
            file_name=filename,
            mime="text/csv"
        )
