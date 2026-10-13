# ui/components/ai_insights_dashboard.py

import streamlit as st
import requests
from datetime import datetime, timedelta
import numpy as np
import json

BASE_URL = "http://localhost:8000"

def render_ai_insights(student, test_scores):
    st.markdown("### 🎓 Personal Performance Insight")

    if not test_scores:
        st.info("No test scores available to analyze.")
        return

    recent_scores = test_scores[-5:]
    trend = "📉 Falling" if recent_scores[-1] < recent_scores[0] else "📈 Improving"
    std_dev = round(np.std(recent_scores), 2)

    if trend == "📉 Falling" or std_dev > 5:
        suggestion = "⚠️ Recommend focused revision in weak areas. Suggest more practice sessions."
    else:
        suggestion = "✅ Scores are consistent. Maintain current study pace with weekly reviews."

    st.markdown(f"""
    - **Student:** {student['name']} (Class {student['class_name']})
    - **Recent Scores:** {recent_scores}
    - **Score Trend:** {trend}
    - **Score Std Dev:** {std_dev}
    - **AI Recommendation:** {suggestion}
    """)

def ai_insights_dashboard():
    st.subheader("🧠 AI Insights Dashboard")
    st.caption("Smart alerts and predictions for tuition performance and engagement.")

    try:
        students = requests.get(f"{BASE_URL}/students/").json()
        test_scores_raw = requests.get(f"{BASE_URL}/test-scores/").json()
        attendance_raw = requests.get(f"{BASE_URL}/attendance/").json()
        todos_raw = requests.get(f"{BASE_URL}/todo/").json()
        fees_raw = requests.get(f"{BASE_URL}/fees/").json()
    except Exception as e:
        st.error(f"❌ Failed to fetch insights: {e}")
        return

    def safely_parse(data_list):
        parsed = []
        for item in data_list:
            if isinstance(item, str):
                try:
                    item = json.loads(item)
                except json.JSONDecodeError:
                    continue
            parsed.append(item)
        return parsed

    # ✅ Safe parsing
    attendance = safely_parse(attendance_raw)
    test_scores = safely_parse(test_scores_raw)
    todos = safely_parse(todos_raw)
    fees = safely_parse(fees_raw)

    end = datetime.today().date()
    start = end - timedelta(days=7)

    st.markdown("### 🚨 Alerts Summary")

    # 1. Missed 3+ classes
    st.markdown("#### ❌ Students Missing ≥3 Classes")
    recent_attendance = [a for a in attendance if a.get("checkin_time")]
    attendance_count = {}
    for a in recent_attendance:
        date_str = a.get("date")
        if not date_str:
            continue
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        if start <= date_obj <= end:
            sid = a.get("student_id")
            attendance_count[sid] = attendance_count.get(sid, 0) + 1

    for student in students:
        sid = student["id"]
        missed = 7 - attendance_count.get(sid, 0)
        if missed >= 3:
            st.warning(f"📌 {student['name']} missed {missed} classes")

    # 2. Low test scores
    st.markdown("#### 📉 Low Performers (Score < 40%)")
    for score in test_scores:
        if score.get("score") is not None and score["score"] < 40:
            student = next((s for s in students if s["id"] == score.get("student_id")), None)
            if student:
                st.error(f"🔻 {student['name']} scored {score['score']} in {score.get('subject', 'Unknown')}")

    # 3. No recent To-Dos
    st.markdown("#### 📝 No To-Do Activity (Last 7 Days)")
    todo_map = {}
    for t in todos:
        sid = t.get("student_id")
        due_date = t.get("due_date")
        if sid and due_date:
            try:
                dt = datetime.strptime(due_date, "%Y-%m-%d").date()
            except ValueError:
                continue
            if dt >= start:
                todo_map[sid] = True

    for student in students:
        if student["id"] not in todo_map:
            st.info(f"🗒️ {student['name']} has no To-Do tasks in the last 7 days")

    # 4. Fee dues
    st.markdown("#### 💸 Fee Dues")
    fee_map = {}
    for f in fees:
        sid = f.get("student_id")
        amount = f.get("amount_paid")
        if sid and isinstance(amount, (int, float)):
            fee_map[sid] = fee_map.get(sid, 0) + amount

    for student in students:
        expected = student.get("fee", 0)
        paid = fee_map.get(student["id"], 0)
        if expected and paid < expected:
            due = expected - paid
            st.warning(f"💰 {student['name']} has ₹{due} due")

    # Optional: Per-student score trend AI summary
    st.markdown("---")
    st.markdown("### 🔎 Individual Performance Review")
    selected_student = st.selectbox("Select Student", students, format_func=lambda s: f"{s['name']} (Class {s['class_name']})")

    if selected_student:
        sid = selected_student["id"]
        s_scores = [s.get("score", 0) for s in test_scores if s.get("student_id") == sid]
        render_ai_insights(selected_student, s_scores)
