# chatbot/langchain_agent_handler.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents import AgentType
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

router = APIRouter(prefix="/query-agent", tags=["Smart Agent"])

# ----------------------------
# Load DB path and API keys from environment
# ----------------------------
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./tuitorin.db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ----------------------------
# Database Connection
# ----------------------------
try:
    engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
    db = SQLDatabase(engine)
except Exception as e:
    raise RuntimeError(f"Database connection failed: {e}")

# ----------------------------
# Choose LLM Model
# ----------------------------
if GROQ_API_KEY:
    llm = ChatGroq(api_key=GROQ_API_KEY, model_name="mixtral-8x7b-32768", temperature=0.3)
elif OPENAI_API_KEY:
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-3.5-turbo", temperature=0.3)
else:
    raise ValueError("Please set OPENAI_API_KEY or GROQ_API_KEY in your environment or .env file.")

# ----------------------------
# Build LangChain SQL Agent
# ----------------------------
agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    agent_type=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

# ----------------------------
# Input Schema
# ----------------------------
class AgentQuery(BaseModel):
    question: str

# ----------------------------
# POST endpoint to ask database
# ----------------------------
@router.post("/")
def ask_database(query: AgentQuery):
    try:
        response = agent_executor.run(query.question)
        return {"question": query.question, "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Error: {str(e)}")
