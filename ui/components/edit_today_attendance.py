# ui/components/edit_today_attendance.py

import streamlit as st
from datetime import datetime, time, date

from app.db import get_db
from app.models import Attendance
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.crud import log_change


def display():
    st.subheader("✏️ Edit Today's Attendance Records")

    db: Session = next(get_db())
    today = date.today()

    # Get today's attendance
    records = db.scalars(
        select(Attendance).where(Attendance.date == today)
    ).all()

    if not records:
        st.info("No attendance records for today.")
        return

    for record in records:
        with st.expander(f"{record.student.name} (ID: {record.student_id})"):
            col1, col2, col3 = st.columns(3)

            with col1:
                new_checkin = st.time_input(
                    "Check-In Time",
                    value=record.checkin_time.time() if record.checkin_time else time(9, 0),
                    key=f"ci_{record.id}"
                )

            with col2:
                new_checkout = st.time_input(
                    "Check-Out Time",
                    value=record.checkout_time.time() if record.checkout_time else time(12, 0),
                    key=f"co_{record.id}"
                )

            with col3:
                if st.button("💾 Save", key=f"save_{record.id}"):
                    # Update times and recalculate duration
                    new_ci_dt = datetime.combine(today, new_checkin)
                    new_co_dt = datetime.combine(today, new_checkout)
                    new_duration = int((new_co_dt - new_ci_dt).total_seconds() // 60)

                    record.checkin_time = new_ci_dt
                    record.checkout_time = new_co_dt
                    record.duration_minutes = max(new_duration, 0)

                    db.commit()
                    db.refresh(record)

                    log_change(
                        db,
                        action="EDIT_ATTENDANCE",
                        details=f"Edited attendance ID {record.id} for student {record.student_id}"
                    )

                    st.success("✅ Attendance updated successfully.")
