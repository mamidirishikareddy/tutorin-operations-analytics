# ui/components/performance_classifier.py

import streamlit as st
import pandas as pd
import requests

API_BASE = "http://localhost:8000"

# Define classification logic
def classify_performance(score):
    if score >= 85:
        return "✅ Excellent"
    elif score >= 60:
        return "⚠️ Average"
    else:
        return "❌ Needs Improvement"

# Generate To-Do advice based on score
def get_feedback_message(score):
    if score >= 85:
        return "Keep up the excellent performance!"
    elif score >= 60:
        return "Revise chapters and attempt mock tests."
    else:
        return "Needs improvement. Practice weak areas."

# Save feedback to To-Do
def save_feedback_as_todo(student_id, message):
    payload = {
        "student_id": student_id,
        "task": message,
        "completed": False
    }
    try:
        res = requests.post(f"{API_BASE}/todo/", json=payload)
        return res.status_code == 200
    except Exception as e:
        st.error(f"❌ Failed to save To-Do: {e}")
        return False

# Main UI component
def show_performance_classifier():
    st.subheader("📊 Performance Classifier")

    try:
        response = requests.get(f"{API_BASE}/test-scores/")
        if response.status_code != 200:
            st.warning("No test scores found.")
            return

        test_data = response.json()
        if not test_data:
            st.info("No test data available.")
            return

        df = pd.DataFrame(test_data)
        df["score"] = df["score"].astype(float)
        df["label"] = df["score"].apply(classify_performance)

        # Merge student info if needed
        student_map = {s["id"]: s["name"] for s in requests.get(f"{API_BASE}/students/").json()}
        df["student_name"] = df["student_id"].map(student_map)

        st.dataframe(df[["student_id", "student_name", "test_name", "score", "label"]], use_container_width=True)

        st.markdown("---")
        st.markdown("### 💬 Send Feedback as To-Do")

        selected_rows = st.multiselect(
            "Select students to send performance feedback:",
            options=df.index,
            format_func=lambda i: f"{df.loc[i]['student_name']} ({df.loc[i]['label']})"
        )

        if st.button("📝 Generate Feedback"):
            if not selected_rows:
                st.warning("Please select at least one student.")
            else:
                for idx in selected_rows:
                    student_id = int(df.loc[idx]["student_id"])
                    message = get_feedback_message(df.loc[idx]["score"])
                    success = save_feedback_as_todo(student_id, message)
                    if success:
                        st.success(f"✅ Feedback sent to {df.loc[idx]['student_name']}")
    except Exception as e:
        st.error(f"Error loading performance data: {e}")
