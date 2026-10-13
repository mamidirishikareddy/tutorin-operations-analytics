# ui/components/freeze_control.py

import streamlit as st
import requests

BASE_URL = "http://localhost:8000"

def display():
    st.subheader("❄️ Freeze / 🔓 Unfreeze Student")

    # ---------------------------
    # Initialize session state safely (without conflict)
    # ---------------------------
    if "freeze_student_id" not in st.session_state:
        default_id = 1  # fallback default
        try:
            # Try to get first student ID from API for a better default
            response = requests.get(f"{BASE_URL}/students/", timeout=5)
            response.raise_for_status()
            students = response.json()
            if students:
                default_id = students[0]["id"]
        except:
            pass
        st.session_state.freeze_student_id = default_id

    # ---------------------------
    # Student ID Input (only use key, no value)
    # ---------------------------
    student_id = st.number_input(
        "🔢 Enter Student ID to Manage",
        min_value=1,
        step=1,
        key="freeze_student_id"
    )

    # ---------------------------
    # Preview Student Info
    # ---------------------------
    student = None
    if st.button("🔍 Preview Student Info"):
        try:
            resp = requests.get(f"{BASE_URL}/students/{student_id}", timeout=5)
            resp.raise_for_status()
            student = resp.json()

            status_text = "✅ Frozen" if student.get("is_frozen") else "❌ Not Frozen"
            st.success(
                f"👨‍🎓 Name: {student['name']} | Class: {student['class_level']} | Status: {status_text}"
            )
        except requests.exceptions.RequestException:
            st.error(f"⚠️ Student ID {student_id} not found or server error.")

    # ---------------------------
    # Freeze / Unfreeze Controls
    # ---------------------------
    col1, col2 = st.columns(2)

    with col1:
        if st.button("❄️ Freeze Student"):
            try:
                res = requests.put(f"{BASE_URL}/freeze/freeze/{student_id}", timeout=5)
                if res.status_code == 200:
                    st.success(f"✅ Student ID {student_id} has been successfully frozen.")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to freeze: {res.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Request failed: {e}")

    with col2:
        if st.button("🔓 Unfreeze Student"):
            try:
                res = requests.put(f"{BASE_URL}/freeze/unfreeze/{student_id}", timeout=5)
                if res.status_code == 200:
                    st.success(f"✅ Student ID {student_id} has been successfully unfrozen.")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to unfreeze: {res.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Request failed: {e}")

    # ---------------------------
    # Freeze/Unfreeze History (Future Feature Placeholder)
    # ---------------------------
    st.markdown("---")
    if st.checkbox("📋 Show Freeze/Unfreeze History (Not implemented)"):
        st.info("🛠️ This feature is not yet available. Backend support is needed.")
