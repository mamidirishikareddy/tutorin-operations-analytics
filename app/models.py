from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Float, Table
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, date

Base = declarative_base()

# ----------------------------
# Association Tables
# ----------------------------
student_tags = Table(
    "student_tags",
    Base.metadata,
    Column("student_id", ForeignKey("students.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

todo_tags = Table(
    "todo_tags",
    Base.metadata,
    Column("todo_id", ForeignKey("todo_items.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

# ----------------------------
# Student Model
# ----------------------------
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    class_level = Column(String, nullable=False)
    house_number = Column(String, nullable=False)
    contact = Column(String, nullable=False)

    parent_name = Column(String, nullable=True)
    parent_relation = Column(String, nullable=True)
    parent_contact = Column(String, nullable=True)
    parent_email = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)
    is_frozen = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    joining_date = Column(Date, nullable=True, default=date.today)
    exit_reason = Column(String, nullable=True)
    reactivated_on = Column(DateTime, nullable=True)

    # Relationships
    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    todos = relationship("ToDoItem", back_populates="student", cascade="all, delete-orphan")
    test_scores = relationship("TestScore", back_populates="student", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=student_tags, back_populates="students")
    fee_config = relationship("StudentFeeConfig", back_populates="student", uselist=False, cascade="all, delete-orphan")
    fee_records = relationship("FeeRecord", back_populates="student", cascade="all, delete-orphan")
    fees = relationship("Fee", back_populates="student", cascade="all, delete-orphan")
    revision_plans = relationship("RevisionPlanner", back_populates="student", cascade="all, delete-orphan")

# ----------------------------
# To-Do Item Model
# ----------------------------
class ToDoItem(Base):
    __tablename__ = "todo_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    due_date = Column(Date, nullable=True)
    attachment_url = Column(String, nullable=True)
    order_index = Column(Integer, default=0)
    is_done = Column(Boolean, default=False)

    student = relationship("Student", back_populates="todos")
    tags = relationship("Tag", secondary=todo_tags, back_populates="todos")

# ----------------------------
# Tag Model
# ----------------------------
class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)

    students = relationship("Student", secondary=student_tags, back_populates="tags")
    todos = relationship("ToDoItem", secondary=todo_tags, back_populates="tags")

# ----------------------------
# Attendance Model
# ----------------------------
class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    date = Column(Date, default=date.today)
    checkin_time = Column(DateTime, nullable=True)
    checkout_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=0)

    student = relationship("Student", back_populates="attendances")

# ----------------------------
# Audit Log Model
# ----------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String, nullable=False)
    details = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# ----------------------------
# Test Score Model ✅ (ONLY once!)
# ----------------------------
class TestScore(Base):
    __tablename__ = "test_scores"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    date = Column(Date, default=date.today)
    remarks = Column(String, default="")

    student = relationship("Student", back_populates="test_scores")

# ----------------------------
# Student Fee Configuration
# ----------------------------
class StudentFeeConfig(Base):
    __tablename__ = "student_fee_configs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), unique=True, nullable=False)
    monthly_fee = Column(Float, nullable=False)
    note = Column(String, default="")

    student = relationship("Student", back_populates="fee_config")

# ----------------------------
# Fee Record / Payments Table
# ----------------------------
class FeeRecord(Base):
    __tablename__ = "fee_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    amount_paid = Column(Float, nullable=False)
    payment_date = Column(Date, default=date.today)
    method = Column(String, default="Cash")
    note = Column(String, default="")
    receipt_number = Column(String, unique=True, nullable=False)

    student = relationship("Student", back_populates="fee_records")

# ----------------------------
# Fee Summary Table
# ----------------------------
class Fee(Base):
    __tablename__ = "fees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    amount_paid = Column(Float, nullable=False)
    due_amount = Column(Float, nullable=False)
    payment_date = Column(Date, default=date.today)
    remarks = Column(String, default="")

    student = relationship("Student", back_populates="fees")

# ----------------------------
# Revision Planner Model
# ----------------------------
class RevisionPlanner(Base):
    __tablename__ = "revision_planner"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    week_start = Column(Date, nullable=False)
    subject = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    is_done = Column(Boolean, default=False)
    notes = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="revision_plans")
