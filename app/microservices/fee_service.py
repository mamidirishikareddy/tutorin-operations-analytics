from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.db import get_db
from app import models, schemas

router = APIRouter(prefix="/fees", tags=["Fees"])

# ----------------------------
# Set Initial Fee Summary for a Student
# ----------------------------
@router.post("/{student_id}/set")
def set_fee_summary(
    student_id: int,
    amount_paid: float,
    due_amount: float,
    remarks: str = "",
    db: Session = Depends(get_db)
):
    student = db.get(models.Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    existing = db.query(models.Fee).filter_by(student_id=student_id).first()
    if existing:
        existing.amount_paid = amount_paid
        existing.due_amount = due_amount
        existing.remarks = remarks
    else:
        fee = models.Fee(
            student_id=student_id,
            amount_paid=amount_paid,
            due_amount=due_amount,
            remarks=remarks
        )
        db.add(fee)

    db.commit()
    return {"message": "Fee summary set successfully"}


# ----------------------------
# Record a New Payment
# ----------------------------
@router.post("/{student_id}/pay")
def record_payment(
    student_id: int,
    amount: float,
    method: str = "Cash",
    note: str = "",
    receipt_number: str = "",
    db: Session = Depends(get_db)
):
    student = db.get(models.Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Add a new payment record to FeeRecord
    payment = models.FeeRecord(
        student_id=student_id,
        amount_paid=amount,
        payment_date=date.today(),
        method=method,
        note=note,
        receipt_number=receipt_number or f"RCPT-{student_id}-{int(date.today().strftime('%Y%m%d'))}"
    )
    db.add(payment)

    # Update summary in Fee table if exists
    fee_summary = db.query(models.Fee).filter_by(student_id=student_id).first()
    if fee_summary:
        fee_summary.amount_paid += amount
        fee_summary.due_amount = max(fee_summary.due_amount - amount, 0)
    else:
        fee_summary = models.Fee(
            student_id=student_id,
            amount_paid=amount,
            due_amount=0,
            remarks="Auto-generated summary from payment"
        )
        db.add(fee_summary)

    db.commit()
    return {"message": "Payment recorded successfully"}


# ----------------------------
# Get Fee Summary for a Student
# ----------------------------
@router.get("/{student_id}/summary")
def get_fee_summary(student_id: int, db: Session = Depends(get_db)):
    fee = db.query(models.Fee).filter_by(student_id=student_id).first()
    if not fee:
        return {"total": 0, "paid": 0, "due": 0}
    return {
        "total": fee.amount_paid + fee.due_amount,
        "paid": fee.amount_paid,
        "due": fee.due_amount
    }


# ----------------------------
# Get All Fee Records (Payments)
# ----------------------------
@router.get("/", response_model=list[schemas.FeeRecordOut])
def get_all_fee_records(db: Session = Depends(get_db)):
    """
    Retrieve all fee payment records (FeeRecord).
    """
    return db.query(models.FeeRecord).all()


# ----------------------------
# (Optional) Get All Fee Summaries
# ----------------------------
@router.get("/summaries", response_model=list[schemas.StudentFeeConfigOut])
def get_all_fee_summaries(db: Session = Depends(get_db)):
    """
    Retrieve all fee summary records (Fee table).
    """
    return db.query(models.Fee).all()

