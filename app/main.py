from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.log_config import get_logger
from app import models
from app.db import init_db, get_db
from sentry_monitoring import init_sentry
from app.utils.receipt_generator import generate_fee_receipt
from app.microservices import todo_service

# Microservice Routers
from app.microservices.student_service import router as student_router
from app.microservices.attendance_service import router as attendance_router
from app.microservices.todo_service import router as todo_router
from app.microservices.audit_service import router as audit_router
from app.microservices.freeze_service import router as freeze_router
from app.microservices.fee_service import router as fee_router
from app.microservices.test_score_service import router as test_score_router
from app.microservices.revision_service import router as revision_router
from app.microservices.suggestion_service import get_smart_suggestions

# Chatbot Routers
from chatbot.chatbot_handler import router as chatbot_router
from chatbot.langchain_agent_handler import router as langchain_agent_router

# --------------------------------
# App Initialization
# --------------------------------
app = FastAPI(
    title="TuitorIN Tuition Management System",
    description="A full-featured tuition management backend with microservices",
    version="1.0.0"
)

# --------------------------------
# Monitoring & Logging
# --------------------------------
init_sentry(environment="development")  # Change to "production" when deploying
logger = get_logger("main")

# --------------------------------
# Middleware
# --------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔐 Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------
# Lifecycle Events
# --------------------------------
@app.on_event("startup")
def startup_event():
    logger.info("🚀 Starting TuitorIN app...")
    init_db()
    logger.info("✅ Database initialized and app is ready.")

@app.on_event("shutdown")
def shutdown_event():
    logger.info("🛑 FastAPI app is shutting down.")

# --------------------------------
# Health Check Endpoint
# --------------------------------
@app.get("/")
def health_check():
    return {"status": "✅ TuitorIN is up and running!"}

# --------------------------------
# Register All Routers
# --------------------------------
def register_routers(app: FastAPI):
    app.include_router(student_router)
    app.include_router(attendance_router)
    app.include_router(todo_router)
    app.include_router(audit_router)
    app.include_router(freeze_router)
    app.include_router(fee_router)
    app.include_router(test_score_router)
    app.include_router(revision_router)
    app.include_router(chatbot_router)
    app.include_router(langchain_agent_router)

register_routers(app)

# --------------------------------
# Smart To-Do Suggestions
# --------------------------------
@app.post("/todo/suggest/")
def suggest_tasks(payload: dict, db: Session = Depends(get_db)):
    student_id = payload.get("student_id")
    input_text = payload.get("input", "")

    if not student_id:
        raise HTTPException(status_code=400, detail="student_id is required.")

    history = db.query(models.ToDoItem).filter(models.ToDoItem.student_id == student_id).all()
    past_tasks = [{"task": t.title} for t in history]

    suggestions = get_smart_suggestions(past_tasks, input_text)
    return {"suggestions": suggestions}

# --------------------------------
# Generate PDF Fee Receipt
# --------------------------------
@app.get("/receipt/{student_id}")
def get_receipt(student_id: int, session: Session = Depends(get_db)):
    student = session.get(models.Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    last_payment = session.query(models.FeeRecord)\
        .filter_by(student_id=student_id)\
        .order_by(models.FeeRecord.payment_date.desc())\
        .first()

    if not last_payment:
        raise HTTPException(status_code=404, detail="No fee record found")

    buffer = generate_fee_receipt(
        student_name=student.name,
        amount=last_payment.amount_paid,
        date_paid=last_payment.payment_date.strftime("%Y-%m-%d"),
        receipt_number=last_payment.receipt_number
    )

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=receipt_{student_id}.pdf"}
    )
