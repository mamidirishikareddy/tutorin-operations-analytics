# ui/routes/student_page.py

import streamlit as st
from ui.i18n_helper import _

from ui.components.add_edit_student_form import student_form
from ui.components.csv_export_button import download_students_csv
from ui.components.student_profile import render_student_profile
from ui.components.student_csv_import import render_csv_import

from app.microservices.student_service import (
    get_all_students,
    create_student,
    update_student,
    delete_student,
    get_student_by_id
)

def render_student_page():
    st.title(_("👨‍🎓 Student Management"))
    students = get_all_students()

    if not students:
        st.info(_("No students found."))
        return

    # -----------------------------
    # Filters
    # -----------------------------
    search_name = st.text_input(_("Search by name"))
    class_options = ["All"] + sorted({s.class_level for s in students})
    search_class = st.selectbox(_("Filter by class"), class_options)

    filtered_students = [
        s for s in students
        if (search_name.lower() in s.name.lower()) and
           (search_class == "All" or s.class_level == search_class)
    ]

    # -----------------------------
    # Add Student
    # -----------------------------
    with st.expander(_("➕ Add New Student")):
        new_data = student_form()
        if new_data:
            create_student(new_data)
            st.success(_("Student added successfully."))
            st.rerun()

    # -----------------------------
    # CSV Import
    # -----------------------------
    with st.expander(_("📥 Import from CSV")):
        render_csv_import()

    # -----------------------------
    # CSV Export
    # -----------------------------
    download_students_csv([{
        "ID": s.id,
        "Name": s.name,
        "Class": s.class_level,
        "House Number": s.house_number,
        "Contact": s.contact,
        "Joining Date": s.joining_date.strftime("%Y-%m-%d") if s.joining_date else "",
        "Is Frozen": s.is_frozen,
        "Is Active": s.is_active,
        "Tags": ", ".join([tag.name for tag in (s.tags or [])])
    } for s in filtered_students])

    # -----------------------------
    # List View
    # -----------------------------
    st.markdown("### 📋 " + _("Student List"))
    for student in filtered_students:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                status = '🟢 Active' if student.is_active else '🔴 Frozen'
                st.write(f"**{student.name}** | Class {student.class_level} | {status}")
                st.caption(f"{_('Joined')}: {student.joining_date.strftime('%d %b %Y') if student.joining_date else 'N/A'} | {_('Phone')}: {student.contact}")
            with col2:
                if st.button(_("👁️ View"), key=f"view_{student.id}"):
                    st.session_state.view_student = student.id

                if st.button(_("✏️ Edit"), key=f"edit_{student.id}"):
                    st.session_state.editing_student = student.id
                    st.rerun()

                if st.button(_("🗑️ Delete"), key=f"delete_{student.id}"):
                    delete_student(student.id)
                    st.warning(_("Student deleted."))
                    st.rerun()

    # -----------------------------
    # Edit Student View
    # -----------------------------
    if "editing_student" in st.session_state:
        student_id = st.session_state.editing_student
        student = get_student_by_id(student_id)
        if student:
            with st.expander(f"{_('Editing')} {student.name}", expanded=True):
                existing_data = {
                    "id": student.id,
                    "name": student.name,
                    "class_level": student.class_level,
                    "house_number": student.house_number,
                    "contact": student.contact,
                    "joining_date": student.joining_date,
                    "is_active": student.is_active,
                    "is_frozen": student.is_frozen,
                    "tags": [tag.name for tag in (student.tags or [])]
                }
                updated = student_form(existing_data=existing_data)
                if updated:
                    update_student(student.id, updated)
                    st.success(_("Student updated successfully."))
                    del st.session_state.editing_student
                    st.rerun()

    # -----------------------------
    # Profile View
    # -----------------------------
    if "view_student" in st.session_state:
        selected = get_student_by_id(st.session_state.view_student)
        if selected:
            render_student_profile(selected)
            if st.button(_("🔙 Back to list")):
                del st.session_state.view_student
                st.rerun()
