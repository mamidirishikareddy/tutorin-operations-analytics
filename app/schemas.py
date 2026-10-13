from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Literal
from datetime import date, datetime

# ----------------------------
# Tag Schemas
# ----------------------------

class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class TagOut(TagBase):
    id: int

    model_config = {
        "from_attributes": True
    }

# ----------------------------
# Student Schemas
# ----------------------------

class StudentBase(BaseModel):
    name: str
    class_level: str
    house_number: str
    contact: str = Field(..., pattern=r'^\d{10}$')
    is_active: bool = True
    is_frozen: bool = False

    parent_name: Optional[str] = None
    parent_relation: Optional[str] = None
    parent_contact: Optional[str] = Field(default=None, pattern=r'^\d{10}$')
    parent_email: Optional[str] = None

class StudentCreate(StudentBase):
    joining_date: Optional[date] = Field(default_factory=date.today)
    tags: Optional[List[str]] = []

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    class_level: Optional[str] = None
    house_number: Optional[str] = None
    contact: Optional[str] = Field(default=None, pattern=r'^\d{10}$')
    is_active: Optional[bool] = None
    is_frozen: Optional[bool] = None
    tags: Optional[List[str]] = None
    joining_date: Optional[date] = None
    exit_reason: Optional[str] = None
    reactivated_on: Optional[datetime] = None

    parent_name: Optional[str] = None
    parent_relation: Optional[str] = None
    parent_contact: Optional[str] = Field(default=None, pattern=r'^\d{10}$')
    parent_email: Optional[str] = None

class StudentOut(BaseModel):
    id: int
    name: str
    class_level: str
    house_number: str
    contact: str
    is_frozen: bool
    is_active: bool
    created_at: Optional[datetime]
    joining_date: Optional[date]
    exit_reason: Optional[str] = None
    reactivated_on: Optional[datetime] = None
    tags: List[TagOut] = []

    parent_name: Optional[str] = None
    parent_relation: Optional[str] = None
    parent_contact: Optional[str] = None
    parent_email: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

# ----------------------------
# Attendance Schemas
# ----------------------------

class AttendanceBase(BaseModel):
    student_id: int
    attendance_date: date
    checkin_time: Optional[datetime] = None
    checkout_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None

class AttendanceCreate(BaseModel):
    student_id: int
    checkin_time: datetime

class AttendanceCheckout(BaseModel):
    student_id: int
    checkout_time: datetime

class AttendanceOut(AttendanceBase):
    id: int

    model_config = {
        "from_attributes": True
    }

# ----------------------------
# To-Do Schemas
# ----------------------------

class ToDoItemBase(BaseModel):
    student_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    is_done: bool = False
    tags: Optional[str] = None
    priority: Optional[str] = Field(default="Medium", pattern="^(High|Medium|Low)$")
    attachment_url: Optional[HttpUrl] = None
    order_index: Optional[int] = 0

class ToDoItemCreate(ToDoItemBase):
    pass

class ToDoItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    is_done: Optional[bool] = None
    tags: Optional[str] = None
    priority: Optional[str] = Field(default=None, pattern="^(High|Medium|Low)$")
    attachment_url: Optional[HttpUrl] = None
    order_index: Optional[int] = None

class ToDoItemOut(ToDoItemBase):
    id: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

# ----------------------------
# Audit Log Schemas
# ----------------------------

class AuditLogBase(BaseModel):
    action: str
    details: str
    timestamp: datetime

class AuditLogOut(AuditLogBase):
    id: int

    model_config = {
        "from_attributes": True
    }

# ----------------------------
# Fee Summary Schema
# ----------------------------

class FeeSummary(BaseModel):
    total: float
    paid: float
    due: float

# ----------------------------
# Test Score Schemas
# ----------------------------

class TestScoreBase(BaseModel):
    subject: str
    score: float
    test_date: Optional[date] = Field(default_factory=date.today)
    remarks: Optional[str] = ""

class TestScoreCreate(TestScoreBase):
    student_id: int

class TestScoreOut(TestScoreBase):
    id: int
    student_id: int

    model_config = {
        "from_attributes": True
    }

# ----------------------------
# Fee & Payment Schemas
# ----------------------------

class StudentFeeConfigBase(BaseModel):
    monthly_fee: float
    note: Optional[str] = ""

class StudentFeeConfigCreate(StudentFeeConfigBase):
    student_id: int

class StudentFeeConfigUpdate(StudentFeeConfigBase):
    pass

class StudentFeeConfigOut(StudentFeeConfigBase):
    id: int
    student_id: int

    model_config = {
        "from_attributes": True
    }

class FeeRecordBase(BaseModel):
    amount_paid: float
    payment_date: Optional[date] = Field(default_factory=date.today)
    method: Optional[Literal["Cash", "UPI", "Bank", "Cheque"]] = "Cash"
    note: Optional[str] = ""
    receipt_number: str

class FeeRecordCreate(FeeRecordBase):
    student_id: int

class FeeRecordOut(FeeRecordBase):
    id: int
    student_id: int

    model_config = {
        "from_attributes": True
    }
