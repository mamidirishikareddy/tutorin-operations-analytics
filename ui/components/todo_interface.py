import streamlit as st
import requests
import datetime
import base64
from ics import Calendar, Event
from app.models import ToDoItem
from app.db import get_db
from sqlalchemy.orm import Session
from datetime import date

BASE_URL = "http://localhost:8000"

def generate_ics(task, due_date, student_name):
    c = Calendar()
    e = Event()
    e.name = f"Task: {task} – {student_name}"
    e.begin = due_date.isoformat()
    e.duration = {"hours": 1}
    e.description = task
    c.events.add(e)
    return str(c)

def display():
    st.subheader("📚 Student To-Do / Homework Tracker")

    # Load students
    try:
        resp = requests.get(f"{BASE_URL}/students/", timeout=5)
        resp.raise_for_status()
        students = resp.json()
    except Exception:
        st.error("❌ Failed to fetch students.")
        return

    active_students = [s for s in students if not s.get("is_frozen", False)]
    if not active_students:
        st.info("No active students.")
        return

    student_options = {f"{s['name']} (Class {s['class_level']})": s['id'] for s in active_students}
    selected_name = st.selectbox("👨‍🎓 Select Student", list(student_options.keys()))
    student_id = student_options[selected_name]
    student = next(s for s in active_students if s['id'] == student_id)
    student_name = student["name"]
    class_level = student["class_level"]

    # Fetch past task titles for smart suggestions
    try:
        history_resp = requests.get(f"{BASE_URL}/todo/student/{student_id}", timeout=5)
        history_resp.raise_for_status()
        past_todos = history_resp.json()
        past_titles = list({t.get("title") for t in past_todos if t.get("title")})
    except:
        past_titles = []

    st.markdown("---")

    # AI Homework Generator
    st.markdown("### 🤖 Generate AI Homework")
    with st.form("ai_homework_form"):
        subject = st.text_input("📘 Subject", placeholder="e.g., Mathematics")
        score = st.slider("📊 Last Test Score (optional)", 0, 100, 75)
        gen_btn = st.form_submit_button("Generate Homework ✨")
        ai_task = ""
        if gen_btn:
            if not subject.strip():
                st.warning("⚠️ Please enter a subject.")
            else:
                try:
                    res = requests.post(
                        f"{BASE_URL}/chatbot/generate-homework",
                        json={"subject": subject, "class_level": class_level, "score": score},
                        timeout=10
                    )
                    res.raise_for_status()
                    ai_task = res.json().get("generated_task", "").strip()
                    if ai_task:
                        st.success("✅ Homework generated!")
                        st.info(f"**{ai_task}**")
                    else:
                        st.error("❌ No task returned from AI.")
                except Exception as e:
                    st.error(f"❌ Failed to generate: {e}")

    st.markdown("---")

    # Add task form
    with st.expander("➕ Add Homework / Task"):
        with st.form("task_form"):
            suggested = st.selectbox("📌 Smart Suggestion", options=[""] + past_titles)
            task = st.text_input("📝 Task Description", value=suggested if suggested else ai_task)
            tag = st.text_input("🏷️ Tag")
            priority = st.selectbox("🔺 Priority", ["Low", "Medium", "High"])
            due_date = st.date_input("📅 Due Date", min_value=datetime.date.today())
            attachment_url = st.text_input("📎 Attachment URL (optional)")
            submitted = st.form_submit_button("✅ Add Task")
            if submitted:
                if not task.strip():
                    st.warning("⚠️ Task cannot be empty.")
                else:
                    payload = {
                        "student_id": student_id,
                        "title": task.strip(),
                        "tag": tag or None,
                        "priority": priority,
                        "due_date": due_date.isoformat(),
                        "attachment_url": attachment_url or None
                    }
                    resp = requests.post(f"{BASE_URL}/todo/", json=payload)
                    if resp.ok:
                        st.success("✅ Task added.")
                        st.experimental_rerun()
                    else:
                        st.error("❌ Failed to add task.")

    # Filters
    with st.expander("🔍 Filter Tasks"):
        selected_tag = st.text_input("🔖 Filter by Tag")
        selected_priority = st.selectbox("🎯 Filter by Priority", ["", "High", "Medium", "Low"])

    # Fetch all tasks
    try:
        todos_resp = requests.get(f"{BASE_URL}/todo/student/{student_id}", timeout=5)
        todos_resp.raise_for_status()
        todos = todos_resp.json()
    except Exception:
        st.error("❌ Failed to load tasks.")
        return

    if not todos:
        st.info("📭 No tasks found.")
        return

    # Apply filters
    if selected_tag:
        todos = [t for t in todos if t.get("tag", "").lower() == selected_tag.lower()]
    if selected_priority:
        todos = [t for t in todos if t.get("priority") == selected_priority]

    # Status Tabs
    today = datetime.date.today()
    tabs = st.tabs(["⏳ Pending", "✅ Done", "🔴 Overdue"])
    for idx, status in enumerate(["pending", "done", "overdue"]):
        with tabs[idx]:
            any_found = False
            for i, todo in enumerate(todos):
                is_done = todo.get("completed", False) or todo.get("is_done", False)
                due_iso = todo.get("due_date")
                due = datetime.date.fromisoformat(due_iso) if due_iso else None
                overdue = due and due < today and not is_done

                show = (
                    (status == "pending" and not is_done and not overdue) or
                    (status == "done" and is_done) or
                    (status == "overdue" and overdue)
                )
                if not show:
                    continue

                any_found = True
                st.markdown("---")
                col1, col2, col3, col4 = st.columns([4, 1, 1, 2])
                with col1:
                    st.markdown(f"**📝 {todo.get('title', '')}**")
                    if todo.get("tag"):
                        st.caption(f"🏷️ Tag: {todo['tag']}")
                    if todo.get("priority"):
                        st.caption(f"🔺 Priority: {todo['priority']}")
                    if due:
                        st.caption(f"📅 Due: {due.strftime('%d %b %Y')}")
                    if todo.get("attachment_url"):
                        st.markdown(f"[📎 Attachment]({todo['attachment_url']})", unsafe_allow_html=True)

                with col2:
                    if i > 0 and st.button("⬆", key=f"up_{todo['id']}"):
                        swap_order(todos, i, i - 1)
                        update_order_backend(todos)
                        st.experimental_rerun()
                    if i < len(todos) - 1 and st.button("⬇", key=f"down_{todo['id']}"):
                        swap_order(todos, i, i + 1)
                        update_order_backend(todos)
                        st.experimental_rerun()

                with col3:
                    if not is_done and st.button("✅ Mark Done", key=f"done_{todo['id']}"):
                        requests.post(f"{BASE_URL}/todo/done/{todo['id']}")
                        st.experimental_rerun()

                with col4:
                    if due:
                        cal_chk = st.checkbox("📅 Add to Calendar", key=f"cal_{todo['id']}")
                        if cal_chk:
                            ics_string = generate_ics(todo.get('title', ''), due, student_name)
                            b64 = base64.b64encode(ics_string.encode()).decode()
                            safe_title = "".join(c for c in todo["title"] if c.isalnum() or c in (" ", "_")).rstrip()
                            href = f'<a href="data:text/calendar;base64,{b64}" download="{safe_title}.ics">⬇ Download ICS</a>'
                            st.markdown(href, unsafe_allow_html=True)

            if not any_found:
                st.info("📭 No tasks in this category.")

def swap_order(lst, i, j):
    lst[i], lst[j] = lst[j], lst[i]

def update_order_backend(todos):
    ordered_ids = [todo['id'] for todo in todos]
    try:
        requests.post(f"{BASE_URL}/todo/reorder", json={"order": ordered_ids})
    except:
        st.error("⚠️ Failed to update task order.")

def count_pending_tasks():
    db: Session = next(get_db())
    today = date.today()
    return db.query(ToDoItem).filter(
        ToDoItem.due_date == today,
        ToDoItem.is_done == False  # ✅ Fixed: changed from 'completed'
    ).count()
