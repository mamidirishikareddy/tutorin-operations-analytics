import streamlit as st
import requests
import datetime
from ui.components import student_profile, add_edit_student_form, csv_export_button

API_URL = "http://localhost:8000/students"

def display():
    st.subheader("👨‍🎓 Manage Students")

    # -----------------------------
    # Add New Student
    # -----------------------------
    with st.expander("➕ Add New Student"):
        add_edit_student_form.render_add_student_form()

    # -----------------------------
    # CSV Export
    # -----------------------------
    st.markdown("#### 📤 Export All Students")
    csv_export_button.render_export_button()

    st.markdown("---")
    st.subheader("📋 Student List")

    # -----------------------------
    # Filters
    # -----------------------------
    show_frozen = st.checkbox("Include frozen students?")
    show_exited = st.checkbox("Include exited students?")

    colf1, colf2 = st.columns(2)
    today = datetime.date.today()
    start_range = colf1.date_input("📅 Joined After", today - datetime.timedelta(days=30))
    end_range = colf2.date_input("📅 Joined Before", today)

    try:
        response = requests.get(f"{API_URL}/", params={"include_frozen": show_frozen}, timeout=5)
        response.raise_for_status()
        students = response.json()
    except Exception:
        st.error("⚠️ Unable to fetch student list.")
        return

    # -----------------------------
    # Filter by Join Date & Status
    # -----------------------------
    filtered_students = []
    for s in students:
        if not show_exited and not s.get("is_active", True):
            continue
        jd = s.get("joining_date")
        if jd:
            try:
                jd_date = datetime.datetime.strptime(jd, "%Y-%m-%d").date()
                if start_range <= jd_date <= end_range:
                    filtered_students.append(s)
            except:
                continue
        else:
            filtered_students.append(s)

    if not filtered_students:
        st.info("No students found in selected range.")
        return

    # -----------------------------
    # Render Student Cards
    # -----------------------------
    for student in filtered_students:
        with st.container():
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 2, 2, 2, 1, 1, 1, 2])

            # Join Date / New Today
            joining_date = student.get("joining_date")
            is_today = False
            days_since = "-"
            if joining_date:
                try:
                    joining_date_obj = datetime.datetime.strptime(joining_date, "%Y-%m-%d").date()
                    is_today = joining_date_obj == today
                    days_since = (today - joining_date_obj).days
                except:
                    pass

            name_line = f"**👤 {student['name']}**"
            if is_today:
                name_line += " &nbsp; 🆕 <span style='color:green'><b>New Today</b></span>"
            col1.markdown(name_line, unsafe_allow_html=True)

            col2.markdown(f"🏫 Class: `{student['class_level']}`")
            col3.markdown(f"🏠 Address: `{student['house_number']}`")

            contact_info = f"📞 `{student['contact']}`\n🗓️ Joined: `{joining_date}`\n🕓 Since: `{days_since} day(s)`"

            if student.get("parent_name"):
                contact_info += f"\n\n👪 `{student['parent_name']}`"
                if student.get("parent_relation"):
                    contact_info += f" ({student['parent_relation']})"
            if student.get("parent_contact"):
                contact_info += f"\n📱 `{student['parent_contact']}`"
            if student.get("parent_email"):
                contact_info += f"\n📧 `{student['parent_email']}`"

            col4.markdown(contact_info)

            # Status Badge
            if not student.get("is_active", True):
                status = '<span style="color:gray;font-weight:bold">⚫ Exited</span>'
            elif student.get("is_frozen"):
                status = '<span style="color:red;font-weight:bold">🔴 Frozen</span>'
            else:
                status = '<span style="color:green;font-weight:bold">🟢 Active</span>'
            col5.markdown(status, unsafe_allow_html=True)

            # Freeze / Unfreeze button
            if student.get("is_active", True):
                freeze_label = "Unfreeze" if student.get("is_frozen") else "Freeze"
                freeze_url = f"http://localhost:8000/freeze/unfreeze/{student['id']}" if student["is_frozen"] else f"http://localhost:8000/freeze/freeze/{student['id']}"
                if col6.button(freeze_label, key=f"{freeze_label}_{student['id']}"):
                    try:
                        requests.put(freeze_url, timeout=5)
                        st.success(f"✅ Student {freeze_label.lower()}d.")
                        st.experimental_rerun()
                    except:
                        st.error(f"❌ Failed to {freeze_label.lower()} student.")
            else:
                col6.markdown("")

            # Exit or Reactivate logic
            if student.get("is_active", True):
                if col7.button("🚪 Exit", key=f"exit_{student['id']}"):
                    st.session_state[f"exit_mode_{student['id']}"] = True

                if st.session_state.get(f"exit_mode_{student['id']}", False):
                    with st.expander(f"📝 Exit Reason for {student['name']}"):
                        reason = st.text_input("Reason:", key=f"exit_reason_{student['id']}")
                        if st.button("Confirm Exit", key=f"confirm_exit_{student['id']}"):
                            if reason.strip():
                                try:
                                    requests.post(f"{API_URL}/{student['id']}/exit", json={"reason": reason}, timeout=5)
                                    st.success(f"🚪 Student exited with reason: {reason}")
                                    st.experimental_rerun()
                                except:
                                    st.error("❌ Failed to exit student.")
                            else:
                                st.warning("⚠️ Please enter a reason to exit.")
            else:
                if col7.button("🔄 Reactivate", key=f"reactivate_{student['id']}"):
                    try:
                        requests.post(f"{API_URL}/{student['id']}/reactivate", timeout=5)
                        st.success("🔄 Student reactivated.")
                        st.experimental_rerun()
                    except:
                        st.error("❌ Failed to reactivate student.")

            # View Profile
            with col8:
                if st.button("👁 View", key=f"view_{student['id']}"):
                    student_profile.render_student_profile(StudentDTO.from_dict(student))


# ----------------------------------
# DTO for Profile Viewer
# ----------------------------------
class StudentDTO:
    def __init__(self, id, name, class_level, house_number, contact, joining_date, is_frozen, is_active,
                 tags=None, parent_name=None, parent_relation=None, parent_contact=None, parent_email=None):
        self.id = id
        self.name = name
        self.class_level = class_level
        self.house_number = house_number
        self.contact = contact
        self.joining_date = datetime.datetime.strptime(joining_date, "%Y-%m-%d").date() if joining_date else None
        self.is_frozen = is_frozen
        self.is_active = is_active
        self.tags = tags or []
        self.parent_name = parent_name
        self.parent_relation = parent_relation
        self.parent_contact = parent_contact
        self.parent_email = parent_email

    @classmethod
    def from_dict(cls, d):
        return cls(
            id=d["id"],
            name=d["name"],
            class_level=d["class_level"],
            house_number=d["house_number"],
            contact=d["contact"],
            joining_date=d.get("joining_date"),
            is_frozen=d.get("is_frozen", False),
            is_active=d.get("is_active", True),
            tags=d.get("tags", []),
            parent_name=d.get("parent_name"),
            parent_relation=d.get("parent_relation"),
            parent_contact=d.get("parent_contact"),
            parent_email=d.get("parent_email")
        )
