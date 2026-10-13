# ui/components/study_planner.py

import streamlit as st
import requests
from datetime import datetime, timedelta

API_URL = "http://localhost:8000"

# Subject templates for classes
STUDY_TOPICS = {
    "6th": ["Math: Fractions", "Science: Living Organisms", "English: Grammar", "Social: Ancient History"],
    "7th": ["Math: Decimals", "Science: Acids & Bases", "English: Comprehension", "Social: Medieval India"],
    "8th": ["Math: Algebra", "Science: Metals & Non-Metals", "English: Essay Writing", "Social: Revolutions"],
    "9th": ["Math: Linear Equations", "Science: Tissues", "English: Poetry", "Social: Nationalism"],
    "10th": ["Math: Trigonometry", "Science: Genetics", "English: Letter Writing", "Social: World Wars"]
}

def generate_plan(subjects, hours_per_day, days):
    """Distribute subjects over given days."""
    plan = []
    current_date = datetime.today()
    total_slots = days * hours_per_day

    chunks = subjects * ((total_slots // len(subjects)) + 1)
    scheduled = chunks[:total_slots]

    for i in range(days):
        date_str = (current_date + timedelta(days=i)).strftime("%Y-%m-%d")
        tasks = scheduled[i * hours_per_day:(i + 1) * hours_per_day]
        plan.append((date_str, tasks))
    return plan

def submit_to_todo(student_id, plan):
    """Push tasks to backend To-Do service."""
    success_count = 0
    for date, tasks in plan:
        for task in tasks:
            payload = {
                "student_id": student_id,
                "title": f"[Study Plan] {task}",
                "description": f"Study task for {task}",
                "due_date": date,
                "is_done": False,
                "priority": "Medium"
            }
            try:
                response = requests.post(f"{API_URL}/todo/", json=payload)
                if response.status_code == 200 or response.status_code == 201:
                    success_count += 1
                else:
                    st.error(f"❌ Failed: {task} — {response.text}")
            except Exception as e:
                st.error(f"❌ Exception: {task} — {str(e)}")
    return success_count

def study_planner_ui():
    st.subheader("📚 AI-Powered Study Planner")

    # Step 1: Fetch students
    try:
        res = requests.get(f"{API_URL}/students/")
        res.raise_for_status()
        students = res.json()
    except Exception as e:
        st.error(f"❌ Cannot fetch students: {str(e)}")
        return

    if not students:
        st.warning("ℹ️ Please add students first.")
        return

    student = st.selectbox(
        "👨‍🎓 Choose Student",
        students,
        format_func=lambda s: f"{s.get('name', 'Unknown')} ({s.get('class_level', 'N/A')})"
    )

    hours_per_day = st.slider("⏱️ Study Hours per Day", 1, 6, 2)
    total_days = st.slider("📅 Plan Duration", 3, 14, 7)

    # Fallback handling for class_level
    class_level = student.get("class_level", "")
    default_subjects = STUDY_TOPICS.get(class_level, ["Math", "Science", "English", "Social"])
    weak_topics = st.text_input("✏️ Custom Topics (comma-separated)", ", ".join(default_subjects))

    if st.button("🧠 Generate Plan"):
        topics = [t.strip() for t in weak_topics.split(",") if t.strip()]
        if not topics:
            st.warning("Please enter at least one valid topic.")
            return

        plan = generate_plan(topics, hours_per_day, total_days)

        st.success("✅ Study plan created!")
        for date, tasks in plan:
            with st.expander(f"📆 {date}"):
                for task in tasks:
                    st.markdown(f"- {task}")

        if st.button("💾 Save Plan to To-Do"):
            total = submit_to_todo(student["id"], plan)
            st.success(f"📝 {total} tasks pushed to To-Do list.")
