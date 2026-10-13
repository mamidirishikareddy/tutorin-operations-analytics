from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from typing import List
import contextlib
from datetime import date, timedelta
import csv
import io  # ✅ Fix: Import 'io' to handle CSV file streams

from app import crud, schemas, models
from app.db import get_db

router = APIRouter(prefix="/students", tags=["Students"])

# ----------------------------
# FastAPI ROUTES
# ----------------------------

@router.post("/", response_model=schemas.StudentOut)
def create_student_api(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    return crud.create_student(db, student)

@router.get("/", response_model=List[schemas.StudentOut])
def read_students(include_frozen: bool = False, db: Session = Depends(get_db)):
    return crud.get_students(db, include_frozen=include_frozen)

@router.get("/{student_id}", response_model=schemas.StudentOut)
def read_student(student_id: int, db: Session = Depends(get_db)):
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.put("/{student_id}", response_model=schemas.StudentOut)
def update_student_api(student_id: int, update_data: schemas.StudentUpdate, db: Session = Depends(get_db)):
    student = crud.update_student(db, student_id, update_data.dict(exclude_unset=True))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.post("/{student_id}/freeze", response_model=schemas.StudentOut)
def freeze_student(student_id: int, db: Session = Depends(get_db)):
    student = crud.freeze_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.post("/{student_id}/unfreeze", response_model=schemas.StudentOut)
def unfreeze_student(student_id: int, db: Session = Depends(get_db)):
    student = crud.unfreeze_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.post("/{student_id}/exit", response_model=schemas.StudentOut)
def exit_student(
    student_id: int,
    reason: dict = Body(..., example={"reason": "Moved to another school"}),
    db: Session = Depends(get_db)
):
    exit_reason = reason.get("reason")
    if not exit_reason:
        raise HTTPException(status_code=400, detail="Exit reason required.")
    student = crud.exit_student(db, student_id, reason=exit_reason)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.post("/{student_id}/reactivate", response_model=schemas.StudentOut)
def reactivate_student(student_id: int, db: Session = Depends(get_db)):
    student = crud.reactivate_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.get("/{student_id}/fee-summary")
def get_fee_summary_api(student_id: int, db: Session = Depends(get_db)):
    summary = crud.get_fee_summary(db, student_id)
    if not summary:
        raise HTTPException(status_code=404, detail="No fee data found")
    return summary

@router.get("/{student_id}/test-scores")
def get_test_scores_api(student_id: int, db: Session = Depends(get_db)):
    return crud.get_test_scores_for_student(db, student_id)

@router.get("/tags", response_model=List[schemas.TagOut])
def get_all_tags(db: Session = Depends(get_db)):
    return db.scalars(select(models.Tag)).all()

@router.post("/students/import_csv")
async def import_students_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    reader = csv.DictReader(io.StringIO((await file.read()).decode()))
    count = 0
    for row in reader:
        student = models.Student(
            name=row["name"].strip(),
            class_level=row["class_level"],
            house_number=row["house_number"].strip(),
            contact=row["contact"].strip(),
            joining_date=row["joining_date"]
        )
        db.add(student)
        db.commit()
        count += 1
    return {"imported": count}

# ----------------------------
# INTERNAL USE (for Streamlit)
# ----------------------------

@contextlib.contextmanager
def db_session():
    db_gen = get_db()
    try:
        db = next(db_gen)
        yield db
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass

def get_all_students(include_frozen=False):
    with db_session() as db:  # ✅ Fix: Use context properly
        query = db.query(models.Student)
        if not include_frozen:
            query = query.filter(models.Student.is_frozen == False)
        return query.all()

def get_student_by_id(student_id: int):
    with db_session() as db:
        return db.query(models.Student).options(selectinload(models.Student.tags)).filter(models.Student.id == student_id).first()

def create_student(student_data: schemas.StudentCreate):
    with db_session() as db:
        return crud.create_student(db, student_data)

def update_student(student_id: int, update_data: schemas.StudentUpdate):
    with db_session() as db:
        return crud.update_student(db, student_id, update_data.dict(exclude_unset=True))

def delete_student(student_id: int):
    with db_session() as db:
        student = crud.get_student_by_id(db, student_id)
        if student:
            db.delete(student)
            db.commit()
            return True
        return False

def get_fee_summary(student_id: int):
    with db_session() as db:
        return crud.get_fee_summary(db, student_id)

def get_test_scores(student_id: int):
    with db_session() as db:
        return crud.get_test_scores_for_student(db, student_id)

def get_latest_fee_record(student_id: int):
    with db_session() as db:
        record = db.query(models.Fee).filter(models.Fee.student_id == student_id).order_by(models.Fee.payment_date.desc()).first()
        if not record:
            return None
        return {
            "receipt_number": record.id,
            "payment_date": record.payment_date.strftime("%d-%m-%Y"),
            "amount_paid": record.amount_paid,
            "method": record.method,
            "note": record.note,
        }

def get_date_of_last_payment(student_id: int):
    with db_session() as db:
        record = db.query(models.Fee).filter(models.Fee.student_id == student_id).order_by(models.Fee.payment_date.desc()).first()
        return record.payment_date if record else None

def send_fee_reminder(student_id: int):
    with db_session() as db:
        student = crud.get_student_by_id(db, student_id)
        if student:
            crud.create_audit_log(
                db=db,
                action="Reminder Sent",
                details=f"Fee reminder sent to {student.name} (Phone: {student.contact})"
            )

def get_expected_next_due(student_id: int):
    last_payment = get_date_of_last_payment(student_id)
    if not last_payment:
        with db_session() as db:
            student = crud.get_student_by_id(db, student_id)
            last_payment = student.joining_date if student else date.today()
    return (last_payment + timedelta(days=30)).strftime('%d-%m-%Y')

def run_auto_fee_reminders():
    today = date.today()
    overdue_students = []

    with db_session() as db:
        students = db.query(models.Student).filter(models.Student.is_active == True).all()

        for student in students:
            last_payment = db.query(models.Fee)\
                .filter(models.Fee.student_id == student.id)\
                .order_by(models.Fee.payment_date.desc())\
                .first()

            days_since_payment = (today - (last_payment.payment_date if last_payment else student.joining_date or today)).days

            if days_since_payment > 30:
                recent_log = db.query(models.AuditLog)\
                    .filter(models.AuditLog.action == "Reminder Sent")\
                    .filter(models.AuditLog.details.like(f"%{student.name}%"))\
                    .order_by(models.AuditLog.timestamp.desc())\
                    .first()

                if not recent_log or (today - recent_log.timestamp.date()).days > 15:
                    crud.create_audit_log(
                        db=db,
                        action="Reminder Sent",
                        details=f"Auto-reminder sent to {student.name} (Phone: {student.contact}) — Overdue {days_since_payment} days"
                    )
                    overdue_students.append({
                        "name": student.name,
                        "days_overdue": days_since_payment,
                        "contact": student.contact
                    })

    return overdue_students
