# 🎓 TuitorIN — Tuition Management System

TuitorIN is a modern, professional-grade **tuition management application** that helps you manage students, attendance, fees, homework, audit logs, and performance dashboards — all from a unified platform.

---

![Streamlit](https://img.shields.io/badge/UI-Streamlit-orange?logo=streamlit)
![FastAPI](https://img.shields.io/badge/API-FastAPI-green?logo=fastapi)
![DuckDB](https://img.shields.io/badge/DB-DuckDB-blue?logo=duckdb)
![Docker](https://img.shields.io/badge/Deployment-Docker-lightblue?logo=docker)

---

## 🚀 Features

* 🧑‍🏫 Student Management (Add, Update, Freeze/Unfreeze)
* 🗕️ Attendance Check-In/Out with duration tracking
* 🧾 Fee Tracking (Date-wise, student-wise)
* ✅ To-Do List / Homework Tracker per student
* 🕵️ Audit Log with timestamped changes
* 📊 Interactive Dashboards (Streamlit + Plotly)
* 📈 External Power BI Dashboard
* 💬 AI Chatbot for queries (LangChain + OpenAI, optional)
* 🔒 Error Monitoring (Loguru for local, Sentry for cloud)
* 📦 Dockerized Deployment

---

## 🧱 Tech Stack

| Layer       | Technology               |
| ----------- | ------------------------ |
| UI          | Streamlit + Plotly       |
| Backend API | FastAPI                  |
| DB          | DuckDB (via SQLModel)    |
| Logging     | Loguru + Audit JSON      |
| Monitoring  | Sentry (optional)        |
| AI Chatbot  | LangChain + OpenAI (opt) |
| Deployment  | Docker                   |

---

## 📁 Directory Structure

```
TuitorIN/
🖁️ app/                    # FastAPI backend
️️️️ main.py
️️️️ models.py
️️️️ crud.py
️️️️ schemas.py
️️️️ db.py
️️️️ audit.py
️️️️ todo.py
️️️️ microservices/
️️️️️️ student_service.py
️️️️️️ attendance_service.py
️️️️️️ todo_service.py
️️️️️️ audit_service.py

🖁️ ui/                     # Streamlit UI
️️️️ streamlit_app.py
️️️️ dashboard_charts.py
️️️️ components/
️️️️️️ student_table.py
️️️️️️ attendance_calendar.py
️️️️️️ todo_interface.py
️️️️️️ audit_viewer.py

🖁️ chatbot/                # Optional Chatbot
️️️️ chatbot_handler.py

🖁️ dashboards/
️️️️ power_bi_dashboard.pbix

🖁️ logs/
️️️️ audit_log.json

🖁️ sentry_monitoring.py
🖁️ Dockerfile
🖁️ docker-compose.yml (optional)
🖁️ requirements.txt
🖁️ .env
🖁️ README.md
```

---

## ⚙️ Setup Instructions

### 🔧 1. Clone and Set Up

```bash
git clone https://github.com/yourusername/TuitorIN.git
cd TuitorIN
```

### 📄 2. Create `.env` File

```env
DB_PATH=tuitorin.db
SENTRY_DSN=your_sentry_dsn_here  # Optional
```

### 📦 3. Install Requirements

```bash
pip install -r requirements.txt
```

### 🚀 4. Run App Locally

Start FastAPI backend:

```bash
uvicorn app.main:app --reload
```

Start Streamlit frontend:

```bash
streamlit run ui/streamlit_app.py
```

---

## 🐳 Docker Deployment

```bash
docker build -t tuitorin .
docker run -p 8000:8000 -p 8501:8501 tuitorin
```

---

## 📊 Dashboards Included

* 📚 Student Count per Class (bar chart)
* 🕒 Weekly Attendance Trend (line graph)
* ✅ Homework Completion (pie chart)
* 📈 Power BI Dashboard (external reports)

---

## 🧠 Optional Chatbot (LangChain)

Enable an AI chatbot to handle tuition queries like fees, timings, etc.

```bash
# Optional usage
python chatbot/chatbot_handler.py
```

---

## 📝 License

This project is released under an open-source license. Use and modify freely.

---

## 👩‍💼 Author

**Rishika Reddy** — Data Science & Full-Stack Developer
🔗 [LinkedIn](https://linkedin.com) (add your link here)
📧 [youremail@example.com](mailto:youremail@example.com)

---
