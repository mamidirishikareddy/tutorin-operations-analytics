import streamlit as st
import requests

def display():
    st.subheader("📖 Currently Studying Students")

    try:
        resp = requests.get("http://localhost:8000/students", params={"include_frozen": False}, timeout=5)
        students = resp.json() if resp.status_code == 200 else []
    except Exception:
        st.error("❌ Failed to fetch student records.")
        return

    if not students:
        st.info("No students are currently studying.")
        return

    for s in students:
        with st.container():
            st.markdown(f"""
            **👤 Name:** {s['name']}  
            **🏫 Class:** {s['class_level']}  
            **🏠 Address:** {s['house_number']}  
            **📞 Contact:** {s['contact']}  
            **🗓️ Joined On:** `{s.get('joining_date', 'N/A')}`  
            **❄️ Status:** {"Frozen" if s['is_frozen'] else "Active"}
            ---
            """)
