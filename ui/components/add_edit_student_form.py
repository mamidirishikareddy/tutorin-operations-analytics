import streamlit as st
from datetime import date
from typing import Optional
from app.schemas import StudentCreate, StudentUpdate
import uuid

def student_form(existing_data: Optional[dict] = None):
    """Reusable form to add/edit a student. Returns schema object on submit."""
    is_edit = existing_data is not None

    # Create a unique key prefix for each form instance
    key_prefix = f"edit_{existing_data.get('id')}" if is_edit and "id" in existing_data else f"add_{uuid.uuid4()}"

    # Input fields with unique keys
    name = st.text_input(
        "👤 Name",
        value=existing_data.get("name", "") if is_edit else "",
        key=f"{key_prefix}_name"
    )

    class_options = ["Nursery", "LKG", "UKG"] + [str(i) for i in range(1, 13)]
    default_class_index = (
        class_options.index(existing_data.get("class_level"))
        if is_edit and existing_data.get("class_level") in class_options else 0
    )
    class_level = st.selectbox(
        "🏫 Class",
        options=class_options,
        index=default_class_index,
        key=f"{key_prefix}_class"
    )

    house_number = st.text_input(
        "🏠 House No. / Address",
        value=existing_data.get("house_number", "") if is_edit else "",
        key=f"{key_prefix}_house"
    )

    contact = st.text_input(
        "📞 Student Contact Number",
        value=existing_data.get("contact", "") if is_edit else "",
        key=f"{key_prefix}_contact"
    )

    # Parent fields
    parent_name = st.text_input(
        "👪 Parent Name",
        value=existing_data.get("parent_name", "") if is_edit else "",
        key=f"{key_prefix}_parent_name"
    )

    parent_relation = st.text_input(
        "📖 Relation to Student",
        value=existing_data.get("parent_relation", "") if is_edit else "",
        key=f"{key_prefix}_parent_relation"
    )

    parent_contact = st.text_input(
        "📱 Parent Contact Number",
        value=existing_data.get("parent_contact", "") if is_edit else "",
        key=f"{key_prefix}_parent_contact"
    )

    parent_email = st.text_input(
        "📧 Parent Email Address",
        value=existing_data.get("parent_email", "") if is_edit else "",
        key=f"{key_prefix}_parent_email"
    )

    joining_date = st.date_input(
        "📅 Joining Date",
        value=existing_data.get("joining_date") if is_edit and existing_data.get("joining_date") else date.today(),
        key=f"{key_prefix}_join_date"
    )

    # Status toggles
    is_active = st.toggle(
        "🟢 Is Active?",
        value=existing_data.get("is_active", True) if is_edit else True,
        key=f"{key_prefix}_is_active"
    )

    is_frozen = st.toggle(
        "❄️ Is Frozen?",
        value=existing_data.get("is_frozen", False) if is_edit else False,
        key=f"{key_prefix}_is_frozen"
    )

    submit_btn = st.button("💾 Save" if is_edit else "➕ Add", key=f"{key_prefix}_submit")

    if submit_btn:
        # Basic Validation
        if not all([name.strip(), class_level.strip(), house_number.strip(), contact.strip()]):
            st.warning("⚠️ All fields are required.")
            return None
        if not contact.isdigit() or len(contact) != 10:
            st.error("🚫 Student contact must be a valid 10-digit number.")
            return None
        if parent_contact and (not parent_contact.isdigit() or len(parent_contact) != 10):
            st.error("🚫 Parent contact must be a valid 10-digit number.")
            return None

        data = {
            "name": name.strip(),
            "class_level": class_level.strip(),
            "house_number": house_number.strip(),
            "contact": contact.strip(),
            "joining_date": joining_date,
            "parent_name": parent_name.strip() or None,
            "parent_relation": parent_relation.strip() or None,
            "parent_contact": parent_contact.strip() or None,
            "parent_email": parent_email.strip() or None,
            "is_active": is_active,
            "is_frozen": is_frozen
        }

        return StudentUpdate(**data) if is_edit else StudentCreate(**data)

    return None
