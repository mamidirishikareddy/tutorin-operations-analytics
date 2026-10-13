# ui/components/test_scores_viewer.py

import streamlit as st
import pandas as pd
import altair as alt
from datetime import date
from app.microservices import test_score_service
from io import BytesIO
import base64
from fpdf import FPDF


# --------------------------------
# Render the Test & Performance Section
# --------------------------------
def render_test_scores(student):
    st.markdown("### 🧪 Test & Performance Report")

    student_id = student.id
    student_name = student.name

    # ---------------------------
    # 1. Add New Test Score
    # ---------------------------
    with st.expander("➕ Add New Test Score"):
        with st.form("add_score_form"):
            subject = st.text_input("📘 Subject")
            score = st.slider("🎯 Score (%)", 0, 100, 50)
            remarks = st.text_input("🗒️ Remarks (optional)")
            submit = st.form_submit_button("✅ Add Score")
            if submit and subject:
                try:
                    test_score_service.add_test_score(student_id, subject, score, remarks=remarks)
                    st.success(f"✅ Added score for **{subject}**!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error adding score: {e}")

    # ---------------------------
    # 2. Fetch & Display Scores
    # ---------------------------
    scores = test_score_service.get_test_scores(student_id)
    if not scores:
        st.info("ℹ️ No test scores yet.")
        return

    df = pd.DataFrame(scores)
    df['score'] = df['score'].astype(float)
    df['timestamp'] = pd.to_datetime(df.get('date', date.today()))  # default to `date` field

    # ---------------------------
    # 3. Average and Performance Label
    # ---------------------------
    avg_score = round(df['score'].mean(), 1)
    st.write(f"📊 **Average Score:** {avg_score}%")

    if avg_score < 40:
        st.error("🔴 Needs Improvement")
    elif avg_score < 70:
        st.warning("🟡 Average")
    else:
        st.success("🟢 Good")

    # ---------------------------
    # 4. Score Trend Chart
    # ---------------------------
    st.markdown("### 📈 Score Trends Over Time")

    animated_chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X("timestamp:T", title="Date"),
        y=alt.Y("score:Q", title="Score (%)"),
        color="subject:N",
        tooltip=["timestamp:T", "subject:N", "score:Q", "remarks:N"]
    ).properties(height=350).interactive()

    st.altair_chart(animated_chart, use_container_width=True)

    # ---------------------------
    # 5. Weak Subject Detection
    # ---------------------------
    weak_subjects = df[df['score'] < 40]['subject'].value_counts()
    if not weak_subjects.empty:
        st.warning("⚠️ Weak Subjects:")
        for subj, count in weak_subjects.items():
            st.write(f"• {subj} — {count} time(s) below 40%")

    # ---------------------------
    # 6. Weekly Revision Plan
    # ---------------------------
    with st.expander("📅 Weekly Revision Plan"):
        plan = df.groupby("subject")["score"].mean().sort_values().head(3).index.tolist()
        st.write("📌 Focus on these subjects this week:")
        for subject in plan:
            st.markdown(f"- 📘 **{subject}**")

    # ---------------------------
    # 7. Syllabus Checklist
    # ---------------------------
    with st.expander("📋 Exam Syllabus Checklist"):
        topics = df['subject'].unique().tolist()
        completed = st.multiselect("✅ Topics Covered", topics)
        percent_done = round((len(completed) / len(topics)) * 100) if topics else 0
        st.progress(percent_done / 100)
        st.info(f"{percent_done}% syllabus marked as complete.")

    # ---------------------------
    # 8. Export CSV & PDF
    # ---------------------------
    with st.expander("📤 Export Report"):
        csv = df.to_csv(index=False).encode()
        st.download_button("⬇️ Download as CSV", csv, file_name=f"{student_name}_scores.csv", mime="text/csv")

        # PDF generation
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, f"{student_name}'s Test Report", ln=True, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, f"Average Score: {avg_score}%", ln=True)

        if avg_score < 40:
            label = "🔴 Needs Improvement"
        elif avg_score < 70:
            label = "🟡 Average"
        else:
            label = "🟢 Good"
        pdf.cell(200, 10, f"Performance: {label}", ln=True)
        pdf.ln(5)

        for index, row in df.iterrows():
            date_str = row.get("date", "") if isinstance(row.get("date"), str) else row.get("timestamp", "")
            pdf.cell(200, 10, f"{row['subject']} ({date_str[:10]}): {row['score']}%", ln=True)

        pdf_bytes = pdf.output(dest="S").encode("latin1")
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{student_name}_test_report.pdf">📄 Download Report Card (PDF)</a>'
        st.markdown(href, unsafe_allow_html=True)

    # ---------------------------
    # 9. Smart Study Planner
    # ---------------------------
    with st.expander("🤖 Smart Study Planner"):
        weak_df = df[df['score'] < 50]
        if weak_df.empty:
            st.success("🎉 No weak areas. Great job!")
        else:
            st.write("⚠️ Suggested Topics to Revise:")
            for subject in weak_df['subject'].unique():
                st.markdown(f"- 🔁 Focus more on **{subject}**")
