import streamlit as st
import requests
from datetime import date
from app.microservices import test_score_service

BASE_URL = "http://localhost:8000/revision"

def display():
    st.subheader("🧪 Revision Planner")

    # --- Auto-suggest weak subjects ---
    st.markdown("#### 🤖 Suggested Subjects to Revise (Based on Test Scores)")
    student_id = st.number_input("Enter Student ID to Analyze", min_value=1, step=1, key="rev_student_id")

    weak_subjects = []
    if student_id:
        try:
            scores = test_score_service.get_test_scores(student_id)
            df = [s for s in scores if s["score"] < 50]
            weak_subjects = sorted(set(s["subject"] for s in df))
            if weak_subjects:
                st.markdown("💡 Based on recent test scores, focus on:")
                for ws in weak_subjects:
                    st.markdown(f"- 📘 **{ws}**")
            else:
                st.success("🎉 No weak subjects detected. Good progress!")
        except Exception as e:
            st.warning(f"⚠️ Could not fetch test scores: {e}")

    st.divider()

    # --- Add New Revision Task ---
    with st.form("add_rev_form"):
        st.markdown("#### ➕ Add Weekly Revision Task")

        subject = st.selectbox(
            "📘 Select Subject",
            options=(weak_subjects + ["Other..."]) if weak_subjects else ["Other..."]
        )

        if subject == "Other...":
            subject = st.text_input("Enter Custom Subject")

        topic = st.text_input("🔍 Topic")
        week_start = st.date_input("🗓️ Week Starting On", value=date.today())
        notes = st.text_area("📝 Notes (optional)")
        submitted = st.form_submit_button("Add Task")

        if submitted:
            if not student_id or not subject or not topic:
                st.warning("⚠️ Please fill in all required fields.")
            else:
                payload = {
                    "student_id": student_id,
                    "subject": subject,
                    "topic": topic,
                    "week_start": week_start.isoformat(),
                    "notes": notes
                }
                try:
                    res = requests.post(f"{BASE_URL}/add", json=payload, timeout=5)
                    res.raise_for_status()
                    st.success("✅ Revision task added!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"❌ Failed to add revision task: {e}")

    st.divider()

    # --- List Revision Tasks ---
    st.markdown("#### 📋 Weekly Revision Tasks")
    filter_student = st.number_input("Filter by Student ID (optional)", min_value=0, value=0, key="filter_student_id")

    try:
        params = {"student_id": filter_student} if filter_student else {}
        res2 = requests.get(f"{BASE_URL}/list", params=params, timeout=5)
        tasks = res2.json() if res2.status_code == 200 else []
    except Exception as e:
        st.error(f"❌ Failed to fetch tasks: {e}")
        tasks = []

    if not tasks:
        st.info("No revision tasks found.")
        return

    for task in tasks:
        with st.container():
            task_id = task["id"]
            week_start = task.get("week_start", "")
            subject = task.get("subject", "")
            topic = task.get("topic", "")

            st.markdown(f"**ID:** {task_id} | **{week_start}** • **{subject} – {topic}**")

            if task.get("notes"):
                st.caption(f"📝 Notes: {task['notes']}")

            cols = st.columns([1, 1, 1])
            if not task.get("is_done"):
                if cols[0].button("✅ Mark Done", key=f"done_{task_id}"):
                    try:
                        requests.put(f"{BASE_URL}/mark_done/{task_id}", timeout=5)
                        st.success("Task marked as done.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"❌ Error marking as done: {e}")
            else:
                cols[0].markdown("✅ Completed")

            if cols[1].button("🗑️ Delete", key=f"del_{task_id}"):
                try:
                    requests.delete(f"{BASE_URL}/delete/{task_id}", timeout=5)
                    st.warning("Task deleted.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"❌ Error deleting task: {e}")
