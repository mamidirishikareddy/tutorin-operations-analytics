from datetime import datetime
from sqlmodel import Session, select

from app.models import Student, FreezeStatus


# ----------------------------
# Freeze a Student
# ----------------------------
def freeze_student(session: Session, student_id: int):
    student = session.get(Student, student_id)
    if not student or student.is_frozen:
        return None  # Already frozen or doesn't exist

    student.is_frozen = True
    freeze_status = FreezeStatus(
        student_id=student_id,
        frozen_on=datetime.now()
    )
    session.add(freeze_status)
    session.commit()
    session.refresh(student)
    return student


# ----------------------------
# Unfreeze a Student
# ----------------------------
def unfreeze_student(session: Session, student_id: int):
    student = session.get(Student, student_id)
    if not student or not student.is_frozen:
        return None  # Not frozen or doesn't exist

    student.is_frozen = False

    # Get the most recent freeze entry (if exists)
    statement = (
        select(FreezeStatus)
        .where(FreezeStatus.student_id == student_id)
        .order_by(FreezeStatus.frozen_on.desc())
    )
    freeze_record = session.exec(statement).first()
    if freeze_record and freeze_record.unfrozen_on is None:
        freeze_record.unfrozen_on = datetime.now()

    session.commit()
    session.refresh(student)
    return student


# ----------------------------
# Get Freeze History
# ----------------------------
def get_freeze_history(session: Session, student_id: int):
    statement = (
        select(FreezeStatus)
        .where(FreezeStatus.student_id == student_id)
        .order_by(FreezeStatus.frozen_on.desc())
    )
    return session.exec(statement).all()
