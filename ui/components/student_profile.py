import streamlit as st
from datetime import date, timedelta
from app.microservices import (
    student_service,
    attendance_service,
    todo_service,
    audit_service
)
from fpdf import FPDF
import base64
from io import BytesIO

# Emoji tags based on relation
parent_emoji_map = {
    "father": "👨‍👦",
    "mother": "👩‍👧",
    "guardian": "🧑‍🏫",
    "uncle": "🧓",
    "aunt": "👵",
    "sibling": "👦",
    "other": "👤"
}

def render_student_profile(student):
    st.markdown("### 🧑 Student Profile", unsafe_allow_html=True)

    days_since_joining = (date.today() - student.joining_date).days if student.joining_date else "N/A"
    st.subheader(f"{student.name} (Class {student.class_level})")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"📅 **Joining Date:** {student.joining_date.strftime('%d-%m-%Y') if student.joining_date else 'N/A'}")
        st.write(f"⏳ **Days Since Joining:** {days_since_joining} days")
        st.write(f"📞 **Phone:** `{student.contact}`")
        st.write(f"🏠 **Address:** {student.house_number}")
    with col2:
        if not student.is_active:
            st.markdown("📌 **Status:** <span style='color:gray; font-weight:bold;'>⚫ Exited</span>", unsafe_allow_html=True)
            st.warning(f"🚪 Exited — Reason: {student.exit_reason or 'Not specified'}")
        elif student.is_frozen:
            st.markdown("📌 **Status:** <span style='color:orange; font-weight:bold;'>🟡 Frozen</span>", unsafe_allow_html=True)
        else:
            st.markdown("📌 **Status:** <span style='color:green; font-weight:bold;'>🟢 Active</span>", unsafe_allow_html=True)

        if student.reactivated_on:
            st.info(f"🔁 Reactivated on: {student.reactivated_on.strftime('%d-%m-%Y')}")

    # 🧑‍🤝‍🧑 Parent Info
    if hasattr(student, "parent_name") and student.parent_name:
        emoji = parent_emoji_map.get(getattr(student, "parent_relation", "other").lower(), "👤")
        st.markdown(f"#### {emoji} Parent Info", unsafe_allow_html=True)
        st.write(f"👨‍👩‍👧 **Name:** {student.parent_name}")
        st.write(f"📞 **Phone:** `{student.parent_contact}`")
        st.write(f"📝 **Relation:** `{student.parent_relation}`")
        st.markdown("---")

    # Attendance
    with st.expander("🕘 Attendance Summary"):
        summary = attendance_service.get_student_attendance_summary(student.id) or {}
        st.write(f"✅ **Total Days Present:** {summary.get('total_present', 0)}")
        st.write(f"⏱️ **Average Daily Study Time:** {summary.get('avg_duration', 0)} mins")

    # Tasks
    with st.expander("📚 Task Summary"):
        todos = todo_service.get_tasks_for_student(student.id) or []
        done = [t for t in todos if t.is_done]
        st.write(f"✅ **Completed:** {len(done)} | ⏳ **Pending:** {len(todos) - len(done)}")

    # Fee Info
    with st.expander("💰 Fee Summary & Insights"):
        fee = student_service.get_fee_summary(student.id) or {}
        st.write(f"💸 **Total Fee:** ₹{fee.get('total', 0)}")
        st.write(f"🟢 **Paid:** ₹{fee.get('paid', 0)}")
        st.write(f"🔴 **Due:** ₹{fee.get('due', 0)}")

        last = student_service.get_latest_fee_record(student.id)
        if last:
            if st.button("🧾 Download Last Fee Receipt"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 14)
                pdf.cell(190, 10, "Tuition Fee Receipt", ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", size=12)
                for k in ["receipt_number", "payment_date", "amount_paid", "method", "note"]:
                    if last.get(k):
                        pdf.cell(190, 8, f"{k.replace('_',' ').title()}: {last[k]}", ln=True)
                data = pdf.output(dest='S').encode('latin1')
                b64 = base64.b64encode(data).decode()
                st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="Fee_Receipt_{student.id}.pdf">📥 Download PDF</a>', unsafe_allow_html=True)
        else:
            st.info("No payments found.")

        config = student_service.get_fee_config(student.id)
        if config:
            monthly = config['monthly_fee']
            joining = student.joining_date or date.today()
            months = max(1, (date.today().year - joining.year) * 12 + date.today().month - joining.month + 1)
            expected = monthly * months
            paid = fee.get("paid", 0)
            if paid < expected * 0.5:
                st.warning("📉 Low Payment Trend")
                st.info(f"Expected by now: ₹{expected} | Paid: ₹{paid}")

        if fee.get("due", 0) > 0:
            last_pay_date = student_service.get_date_of_last_payment(student.id) or student.joining_date
            overdue_days = (date.today() - last_pay_date).days if last_pay_date else 0
            if overdue_days > 30:
                st.error(f"⚠️ Fee overdue by {overdue_days} days!")
                if st.button("🔔 Send Fee Reminder"):
                    student_service.send_fee_reminder(student.id)
                    st.success("Reminder Sent ✅")

    # Test Scores
    with st.expander("📊 Test Performance"):
        scores = student_service.get_test_scores(student.id) or []
        if scores:
            avg = round(sum(s['score'] for s in scores) / len(scores), 1)
            st.write(f"📈 **Average Score:** {avg}%")
            if avg < 40:
                st.warning("⚠️ Needs Improvement")
            elif avg < 70:
                st.info("🟡 Average")
            else:
                st.success("🟢 Good")
        else:
            st.info("No test scores available.")

    # Activity Logs
    with st.expander("🧾 Recent Activity Logs"):
        logs = audit_service.get_logs_for_student(student.id) or []
        logs = sorted(logs, key=lambda l: l.get("timestamp", ""), reverse=True)
        if logs:
            for log in logs[:5]:
                st.markdown(f"- 📝 **[{log.get('timestamp', '')}]** {log.get('action', '')}")
        else:
            st.info("No audit logs found.")

    # PDF Export
    def generate_pdf(student, summary, todos, fee, scores, logs):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, f"Student Profile - {student.name}", ln=True, align='C')
        pdf.set_font("Arial", size=12)

        pdf.ln(5)
        pdf.cell(200, 10, f"Class: {student.class_level}", ln=True)
        pdf.cell(200, 10, f"Phone: {student.contact}", ln=True)
        pdf.cell(200, 10, f"Address: {student.house_number}", ln=True)
        pdf.cell(200, 10, f"Joining Date: {student.joining_date.strftime('%d-%m-%Y') if student.joining_date else 'N/A'}", ln=True)
        pdf.cell(200, 10, f"Status: {'Exited' if not student.is_active else ('Frozen' if student.is_frozen else 'Active')}", ln=True)

        if hasattr(student, "parent_name"):
            pdf.cell(200, 10, f"Parent: {student.parent_name} ({student.parent_relation})", ln=True)
            pdf.cell(200, 10, f"Parent Contact: {student.parent_contact}", ln=True)

        pdf.ln(3)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, "Attendance Summary", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, f"Days Present: {summary.get('total_present', 0)}", ln=True)
        pdf.cell(200, 10, f"Average Duration: {summary.get('avg_duration', 0)} mins", ln=True)

        pdf.ln(3)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, "Fee Summary", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, f"Total: ₹{fee.get('total', 0)} | Paid: ₹{fee.get('paid', 0)} | Due: ₹{fee.get('due', 0)}", ln=True)

        pdf.ln(3)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, "Tasks", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, f"Completed: {len([t for t in todos if t.is_done])}, Pending: {len([t for t in todos if not t.is_done])}", ln=True)

        pdf.ln(3)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, "Test Scores", ln=True)
        pdf.set_font("Arial", size=12)
        if scores:
            avg = round(sum(s['score'] for s in scores) / len(scores), 1)
            pdf.cell(200, 10, f"Average Score: {avg}%", ln=True)
        else:
            pdf.cell(200, 10, "No test scores available.", ln=True)

        pdf.ln(3)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, "Recent Activity Logs", ln=True)
        pdf.set_font("Arial", size=12)
        for log in logs[:5]:
            ts = log.get("timestamp", "")
            action = log.get("action", "")
            pdf.cell(200, 10, f"{ts}: {action}", ln=True)

        return pdf.output(dest='S').encode('latin1')

    if st.button("📄 Download Profile as PDF"):
        pdf_bytes = generate_pdf(
            student,
            summary,
            todos,
            fee,
            scores,
            logs
        )
        b64_pdf = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{student.name}_profile.pdf">📥 Click here to download PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

    # Expected due
    next_due = student_service.get_expected_next_due(student.id)
    if next_due:
        st.info(f"⏭️ **Next Expected Due Date:** {next_due}")

    # Mobile responsive CSS
    st.markdown("""
    <style>
        @media (max-width: 768px) {
            .stColumn { display: block !important; width: 100% !important; }
        }
    </style>
    """, unsafe_allow_html=True)
