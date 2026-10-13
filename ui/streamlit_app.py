# ui/streamlit_app.py

import re
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st

from datetime import datetime
from ui.i18n_helper import _  # Translation function

# ---------------------------
# Theme & Auth
# ---------------------------
from ui.auth_helper import initialize_authenticator
from ui.components import theme_toggle
theme_toggle.apply_theme()  # ✅ Apply once globally

# ---------------------------
# Dark/Light Mode Styling (fallback)
# ---------------------------
def apply_theme():
    if st.session_state.get("profile_theme", "Light") == "Dark":
        st.markdown("""
            <style>
            body, .stApp { background-color: #0e1117; color: white; }
            .stButton>button { background-color: #262730; color: white; }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            body, .stApp { background-color: white; color: black; }
            </style>
        """, unsafe_allow_html=True)
apply_theme()

# ---------------------------
# Authenticator
# ---------------------------
authenticator = initialize_authenticator()
authenticator.login(location="main")

if st.session_state.get("authentication_status"):
    st.sidebar.success(f"👋 {_('welcome')}, {st.session_state['name']}")
elif st.session_state.get("authentication_status") is False:
    st.error(_("login_failed"))
    st.stop()
elif st.session_state.get("authentication_status") is None:
    st.warning(_("login_prompt"))
    st.stop()

with st.sidebar:
    authenticator.logout(_("logout"), "sidebar")

# ---------------------------
# Component Imports
# ---------------------------
from ui.components import (
    attendance_calendar,
    attendance_status_summary,
    todo_interface,
    audit_viewer,
    freeze_control,
    chatbot_ui,
    student_summary,
    pending_checkout,
    edit_today_attendance,
    attendance_export,
    fees_tab,
    test_scores_viewer,
    powerbi_dashboard
)
from ui.components.add_edit_student_form import student_form
from ui.components.csv_export_button import download_students_csv
from ui.components.student_profile import render_student_profile
from ui.components.revision_planner import display as revision_planner_display
from ui.components.study_planner import study_planner_ui
from ui.components.performance_classifier import show_performance_classifier
from ui.components.ai_insights_dashboard import render_ai_insights, ai_insights_dashboard
from ui.components.student_csv_import import render_csv_import
from ui.dashboard_charts import show_dashboard

# ---------------------------
# Backend Services
# ---------------------------
from app.microservices.student_service import (
    get_all_students,
    create_student,
    update_student,
    delete_student,
    get_student_by_id
)

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(
    page_title=_("dashboard_title"),
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------
# Notifications
# ---------------------------
st.sidebar.markdown("## 🔔 Notifications")
try:
    pending_tasks = todo_interface.count_pending_tasks()
except:
    pending_tasks = 0

try:
    upcoming_tests = test_scores_viewer.count_upcoming_tests()
except:
    upcoming_tests = 0

if pending_tasks:
    st.sidebar.warning(f"📝 {pending_tasks} Pending To-Do(s)")
if upcoming_tests:
    st.sidebar.info(f"🧪 {upcoming_tests} Upcoming Test(s)")
if not pending_tasks and not upcoming_tests:
    st.sidebar.success("✅ All caught up!")

# ---------------------------
# Top-right Bell Icon
# ---------------------------
st.markdown("""
    <style>
    .top-right-bell {
        position: fixed;
        top: 10px;
        right: 20px;
        font-size: 22px;
        z-index: 1000;
        color: #f39c12;
    }
    </style>
    <div class='top-right-bell'>🔔</div>
""", unsafe_allow_html=True)

# ---------------------------
# Sidebar Navigation
# ---------------------------
# Dashboard always first
DASHBOARD_PAGE = "📊 Dashboard"

# Other pages to be sorted
OTHER_PAGES = [
    "👨‍🎓 Students",
    "👥 Student Summary",
    "🕘 Attendance",
    "📝 To-Do",
    "🧪 Test Scores",
    "💰 Fees",
    "🎓 Performance Labels",
    "🧾 Audit Logs",
    "🧊 Freeze Control",
    "💬 Chatbot",
    "🧠 AI Insights",
    "📅 Revision Planner",
    "📚 Study Planner"
]

# Sort other pages ignoring emojis
def strip_emoji(label):
    return re.sub(r"^[^\w\s]+", "", label).strip().lower()

SORTED_PAGES = [DASHBOARD_PAGE] + sorted(OTHER_PAGES, key=strip_emoji)

if "current_page" not in st.session_state:
    st.session_state["current_page"] = SORTED_PAGES[0]

with st.sidebar:
    st.markdown("### 📂 " + _("select_page"))
    for pg in SORTED_PAGES:
        if st.button(pg, key=f"page_btn_{pg}"):
            st.session_state["current_page"] = pg
            st.rerun()

# ---------------------------
# Language Selector
# ---------------------------
lang_display = ["English", "Hindi", "Telugu", "Tamil"]
lang_codes = {"English": "en", "Hindi": "hi", "Telugu": "te", "Tamil": "ta"}
current_lang = next(k for k, v in lang_codes.items() if v == st.session_state.get("lang", "en"))

selected_lang = st.sidebar.selectbox("🌐 Language", lang_display, index=lang_display.index(current_lang))
new_lang_code = lang_codes[selected_lang]

if st.session_state.get("lang") != new_lang_code:
    st.session_state["lang"] = new_lang_code
    st.rerun()

# ---------------------------
# Page Routing
# ---------------------------
page = st.session_state["current_page"]

if page == "📊 Dashboard":
    st.markdown(f"""
        <h2 style='margin-bottom:0;'>👋 Welcome, {st.session_state['name']}!</h2>
        <h5 style='color:gray;'>{datetime.now().strftime("%A, %d %B %Y | %I:%M %p")}</h5>
        <hr style='margin-top:0;margin-bottom:1rem;'>
    """, unsafe_allow_html=True)

    search_input = st.text_input("🔍 Search students, tasks, tests (type at least 3 letters)...")
    if search_input and len(search_input) >= 3:
        st.info(f"Showing results for: `{search_input}`")
        st.markdown("- 📘 [Mock Result] Student: Rohan (Class 10)")
        st.markdown("- 📝 [Mock Result] Task: Submit homework")
        st.markdown("- 🧪 [Mock Result] Test: Science - July 6")
        st.divider()

    with st.container():
        col1, col2, col3 = st.columns(3)
        col1.metric("👨‍🎓 Total Students", len(get_all_students()))
        col2.metric("🟢 Present Today", attendance_status_summary.count_present_today())
        col3.metric("📝 Pending To-Dos", todo_interface.count_pending_tasks())

    st.markdown("### 📅 Today's Schedule")
    st.markdown("- 🕙 **10:00 AM** – Class 10 Maths")
    st.markdown("- 🕛 **12:00 PM** – Class 9 Science")
    st.markdown("- 🕔 **05:00 PM** – Homework Review")

    st.divider()
    st.subheader("📈 Student Performance Snapshot")
    show_dashboard()

    st.divider()
    st.markdown(f"""
        <div style='background-color:#f0f2f6; padding: 1rem; border-radius: 0.5rem;'>
            💬 <i>“Success is the sum of small efforts, repeated day-in and day-out.”</i>
        </div>
    """, unsafe_allow_html=True)

elif page == "👨‍🎓 Students":
    from ui.routes.student_page import render_student_page
    render_student_page()

elif page == "👥 Student Summary":
    student_summary.display()

elif page == "🕘 Attendance":
    st.subheader(_("attendance_calendar"))
    attendance_calendar.display()
    st.divider()
    with st.expander(_("today_status"), expanded=True):
        attendance_status_summary.display()
    st.divider()
    with st.expander(_("pending_checkout")):
        pending_checkout.display()
    st.divider()
    with st.expander(_("edit_today")):
        edit_today_attendance.display()
    st.divider()
    with st.expander(_("export_attendance")):
        attendance_export.export_all_attendance()

elif page == "📝 To-Do":
    todo_interface.display()

elif page == "🧪 Test Scores":
    st.title(_("test_scores_title"))
    students = get_all_students()
    selected_student = st.selectbox(_("select_student"), students, format_func=lambda s: f"{s.name} (Class {s.class_level})")
    if selected_student:
        test_scores_viewer.render_test_scores(selected_student)
        st.divider()
        st.subheader(_("ai_insights"))
        test_scores = selected_student.test_scores or []
        render_ai_insights(selected_student, test_scores)

elif page == "💰 Fees":
    fees_tab.display()

elif page == "🧾 Audit Logs":
    audit_viewer.display()

elif page == "🧊 Freeze Control":
    freeze_control.display()

elif page == "💬 Chatbot":
    chatbot_ui.display()

elif page == "🧠 AI Insights":
    ai_insights_dashboard()

elif page == "📅 Revision Planner":
    revision_planner_display()

elif page == "📚 Study Planner":
    study_planner_ui()

elif page == "🎓 Performance Labels":
    show_performance_classifier()

elif page == "📊 Power BI Dashboard":
    powerbi_dashboard.display()

