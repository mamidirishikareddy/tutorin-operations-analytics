import streamlit as st
from datetime import date, timedelta
from app.microservices import student_service


def render_due_students_dashboard():
    st.markdown("## 🔔 Fee Due Dashboard")

    students = student_service.get_all_students()
    due_data = []

    for student in students:
        if not student.is_active:
            continue  # Skip exited students

        fee = student_service.get_fee_summary(student.id)
        if not fee or fee.get("due", 0) <= 0:
            continue

        last_paid = student_service.get_date_of_last_payment(student.id) or student.joining_date
        days_overdue = (date.today() - last_paid).days
        next_due_date = (last_paid + timedelta(days=30)).strftime('%d-%m-%Y')

        due_data.append({
            "Name": student.name,
            "Class": student.class_level,
            "Contact": student.contact,
            "Joining Date": student.joining_date.strftime('%d-%m-%Y') if student.joining_date else "N/A",
            "Due Amount": f"₹{fee['due']}",
            "Days Overdue": days_overdue,
            "Next Due Date": next_due_date,
        })

    if due_data:
        st.write(f"📋 Found **{len(due_data)}** students with pending fees.")
        due_data = sorted(due_data, key=lambda x: x["Days Overdue"], reverse=True)
        st.dataframe(due_data, use_container_width=True)
    else:
        st.success("✅ All students are fee-clear as of today!")
