# app/db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get the database path from environment or fallback
DATABASE_PATH = os.getenv("DB_PATH", "tuitorin.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create SQLAlchemy engine and session factory
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

# Initialize tables
def init_db():
    print("📍 Creating tables using SQLAlchemy...")
    Base.metadata.create_all(engine)
    print("✅ Tables created successfully.")

# FastAPI Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Streamlit / internal use
def get_session():
    return SessionLocal()
