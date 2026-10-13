# app/microservices/freeze_service.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.crud import freeze_student, unfreeze_student, get_student_by_id
from app.schemas import StudentOut

router = APIRouter(prefix="/freeze", tags=["Freeze Control"])

# ----------------------------
# Freeze a Student
# ----------------------------
@router.put("/freeze/{student_id}", response_model=StudentOut)
def freeze(student_id: int, db: Session = Depends(get_db)):
    """
    Freeze a student to disable activity temporarily.
    """
    student = get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return freeze_student(db, student_id)

# ----------------------------
# Unfreeze a Student
# ----------------------------
@router.put("/unfreeze/{student_id}", response_model=StudentOut)
def unfreeze(student_id: int, db: Session = Depends(get_db)):
    """
    Unfreeze a student to resume normal activity.
    """
    student = get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return unfreeze_student(db, student_id)
