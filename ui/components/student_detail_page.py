# ui/components/student_detail_page.py

import streamlit as st
from app.microservices import student_service

def show_student_detail(student_id: int):
    student = student_service.get_student_by_id(student_id)
    if not student:
        st.error("Student not found.")
        return

    from .student_profile import render_student_profile
    render_student_profile(student)
