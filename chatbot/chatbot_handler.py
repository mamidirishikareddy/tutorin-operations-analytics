# chatbot/chatbot_handler.py

import os
from datetime import date, timedelta

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.microservices.student_service import get_all_students
from app.microservices.attendance_service import get_attendance_by_date

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

# Optional: Suppress known harmless deprecation warning
import warnings
try:
    from langchain_core._api import LangChainDeprecationWarning
    warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)
except ImportError:
    pass  # Safe to ignore if LangChain doesn't emit that warning version

# -------------------------------
# Load Environment Variables
# -------------------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ Groq API key not found in .env")

# -------------------------------
# Initialize Groq LLM
# -------------------------------
try:
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model_name="mixtral-8x7b-32768",
        temperature=0.4
    )
except Exception as e:
    raise RuntimeError(f"❌ Failed to initialize Groq LLM: {str(e)}")

# -------------------------------
# Prompt Templates
# -------------------------------
qa_prompt = PromptTemplate.from_template("""
You are a helpful assistant for a tuition management system.

You can answer questions related to:
- student class timings
- fee due details
- joining dates
- attendance summaries

If unsure, respond: "Please check the system records."

User Question: {query}
""")
qa_chain = qa_prompt | llm

homework_prompt = PromptTemplate.from_template("""
You are helping generate personalized homework for a student.

Based on subject, class level, and last test score, suggest one specific, effective task.

Subject: {subject}
Class Level: {class_level}
Last Score: {score}

Only respond with the task. Do not add explanations.
""")
homework_chain = homework_prompt | llm

# -------------------------------
# FastAPI Router Setup
# -------------------------------
router = APIRouter(prefix="/chatbot", tags=["Chatbot / Smart Assistant"])

# -------------------------------
# Pydantic Schemas
# -------------------------------
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str

class HomeworkRequest(BaseModel):
    subject: str
    class_level: int
    score: int

class HomeworkResponse(BaseModel):
    generated_task: str

# -------------------------------
# Smart Q&A Chat Endpoint
# -------------------------------
@router.post("/chat", response_model=ChatResponse)
def handle_chat(req: ChatRequest):
    query = req.query.lower()

    # Custom Rule: Missed Classes
    if "missed" in query and "class" in query:
        try:
            students = get_all_students()
            today = date.today()
            count_map = {}

            for offset in range(7):
                check_date = today - timedelta(days=offset)
                daily_records = get_attendance_by_date(check_date)

                for record in daily_records:
                    if getattr(record, "checkin_time", None):
                        sid = getattr(record, "student_id", None)
                        if sid:
                            count_map[sid] = count_map.get(sid, 0) + 1

            result = []
            for student in students:
                attended = count_map.get(student.id, 0)
                missed = 7 - attended
                if missed >= 3:
                    result.append(f"🔸 {student.name} missed {missed} classes")

            if result:
                return {"response": "📌 Students who missed 3+ classes this week:\n" + "\n".join(result)}
            else:
                return {"response": "✅ No students missed 3 or more classes this week."}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching attendance: {str(e)}")

    # General Q&A via LLM
    try:
        result = qa_chain.invoke({"query": req.query})
        return {"response": str(result).strip() or "Please check the system records."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")

# -------------------------------
# AI Homework Generator Endpoint
# -------------------------------
@router.post("/generate-homework", response_model=HomeworkResponse)
def generate_homework(req: HomeworkRequest):
    try:
        result = homework_chain.invoke({
            "subject": req.subject,
            "class_level": req.class_level,
            "score": req.score
        })
        return {"generated_task": str(result).strip() or "No homework generated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Homework generation error: {str(e)}")
