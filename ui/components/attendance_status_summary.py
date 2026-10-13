# ui/components/attendance_status_summary.py

import streamlit as st
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Student, Attendance

def count_present_today():
    """Utility to count students who checked in today (used on Dashboard)"""
    db: Session = next(get_db())
    today = date.today()
    return db.query(Attendance).filter(Attendance.date == today).count()

def display():
    st.markdown("### 🚦 Attendance Status Summary")

    db: Session = next(get_db())
    today = date.today()

    # Fetch all active students
    all_students = db.execute(
        select(Student).where(Student.is_active == True)
    ).scalars().all()
    all_student_ids = {s.id for s in all_students}

    # Fetch today's attendance
    todays_records = db.execute(
        select(Attendance).where(Attendance.date == today)
    ).scalars().all()

    checked_out = []
    still_inside = []
    marked_ids = set()

    for record in todays_records:
        marked_ids.add(record.student_id)
        if record.checkout_time:
            checked_out.append(record.student)
        else:
            still_inside.append(record.student)

    # Determine absentees
    absent_ids = all_student_ids - marked_ids
    absent_students = db.execute(
        select(Student).where(Student.id.in_(absent_ids))
    ).scalars().all()

    # Display summaries
    col1, col2, col3 = st.columns(3)

    with col1:
        st.success(f"🟢 Checked Out: {len(checked_out)}")
        for s in checked_out:
            st.markdown(f"- {s.name}")

    with col2:
        st.warning(f"🕓 Still Inside: {len(still_inside)}")
        for s in still_inside:
            st.markdown(f"- {s.name}")

    with col3:
        st.error(f"🔴 Absent: {len(absent_students)}")
        for s in absent_students:
            st.markdown(f"- {s.name}")
