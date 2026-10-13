# app/microservices/attendance_service.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List

from app import crud, schemas, models
from app.db import get_db

# ----------------------------
# 📌 Router Declaration
# ----------------------------
router = APIRouter(prefix="/attendance", tags=["Attendance"])

# ----------------------------
# ✅ Mark Student Check-In
# ----------------------------
@router.post("/mark", response_model=schemas.AttendanceOut)
def mark_attendance(data: schemas.AttendanceCreate, db: Session = Depends(get_db)):
    student = crud.get_student_by_id(db, data.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if data.checkin_time > datetime.now():
        raise HTTPException(status_code=400, detail="Check-in time cannot be in the future.")

    records = crud.get_attendance_by_student(db, data.student_id)
    if any(r.date == date.today() and r.checkin_time is not None for r in records):
        raise HTTPException(status_code=400, detail="Check-in already marked for today.")

    return crud.mark_attendance(db, data.student_id, data.checkin_time)

@router.post("/check-in", response_model=schemas.AttendanceOut)
def checkin_alias(data: schemas.AttendanceCreate, db: Session = Depends(get_db)):
    return mark_attendance(data, db)

# ----------------------------
# ✅ Mark Student Check-Out
# ----------------------------
@router.post("/checkout", response_model=schemas.AttendanceOut)
def mark_checkout(data: schemas.AttendanceCheckout, db: Session = Depends(get_db)):
    student = crud.get_student_by_id(db, data.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    try:
        return crud.mark_checkout(db, data.student_id, data.checkout_time)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ----------------------------
# ✅ Get Attendance by Student
# ----------------------------
@router.get("/student/{student_id}", response_model=List[schemas.AttendanceOut])
def get_attendance_by_student(student_id: int, db: Session = Depends(get_db)):
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return crud.get_attendance_by_student(db, student_id)

# ----------------------------
# ✅ Get Attendance by Date
# ----------------------------
@router.get("/date/{target_date}", response_model=List[schemas.AttendanceOut])
def get_attendance_by_date(target_date: date, db: Session = Depends(get_db)):
    return crud.get_attendance_by_date(db, target_date)

# ----------------------------
# ✅ Get All Attendance Records (/attendance/)
# ----------------------------
@router.get("/", response_model=List[schemas.AttendanceOut])
def get_all_attendance(db: Session = Depends(get_db)):
    return crud.get_all_attendance(db)

# ----------------------------
# ✅ Alias: Get All Attendance (/attendance/all)
# ----------------------------
@router.get("/all", response_model=List[schemas.AttendanceOut])
def get_all_attendance_alias(db: Session = Depends(get_db)):
    return crud.get_all_attendance(db)

# ----------------------------
# ✅ Get Students Pending Checkout
# ----------------------------
@router.get("/pending-checkouts", response_model=List[schemas.AttendanceOut])
def get_students_pending_checkout(db: Session = Depends(get_db)):
    today = date.today()
    all_today = crud.get_attendance_by_date(db, today)
    return [a for a in all_today if a.checkout_time is None]

# ----------------------------
# ✅ Attendance Summary for Student
# ----------------------------
@router.get("/summary/{student_id}")
def get_summary(student_id: int, db: Session = Depends(get_db)):
    return crud.get_student_attendance_summary(db, student_id)

# ----------------------------
# ✅ Edit Attendance
# ----------------------------
@router.put("/edit/{attendance_id}", response_model=schemas.AttendanceOut)
def edit_attendance(attendance_id: int, data: schemas.AttendanceOut, db: Session = Depends(get_db)):
    record = db.get(models.Attendance, attendance_id)
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    record.checkin_time = data.checkin_time
    record.checkout_time = data.checkout_time
    record.duration_minutes = data.duration_minutes
    db.commit()
    db.refresh(record)
    return record

# ----------------------------
# ✅ Attendance in Date Range
# ----------------------------
@router.get("/range", response_model=List[schemas.AttendanceOut])
def get_attendance_for_period(start_date: date, end_date: date, db: Session = Depends(get_db)):
    return crud.get_attendance_range(db, start_date, end_date)
