from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, extract
from datetime import datetime, date, timedelta
from pytz import timezone
from typing import Optional, List
from app import crud 

from app.models import (
    Student,
    Attendance,
    ToDoItem,
    AuditLog,
    StudentFeeConfig,
    FeeRecord,
    TestScore,
    Tag
)
from app.schemas import (
    StudentCreate,
    ToDoItemCreate,
    ToDoItemUpdate,
    StudentFeeConfigCreate,
    StudentFeeConfigUpdate,
    FeeRecordCreate
)

# ----------------------------
# Student CRUD
# ----------------------------

def create_student(db: Session, student: StudentCreate):
    db_student = Student(
        name=student.name,
        class_level=student.class_level,
        house_number=student.house_number,
        contact=student.contact,
        joining_date=student.joining_date
    )

    if student.tags:
        existing_tags = db.query(Tag).filter(Tag.name.in_(student.tags)).all()
        existing_tag_names = {tag.name for tag in existing_tags}
        new_tags = [Tag(name=tag_name) for tag_name in student.tags if tag_name not in existing_tag_names]
        db.add_all(new_tags)
        db.flush()
        db_student.tags = existing_tags + new_tags

    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    log_change(db, "CREATE_STUDENT", f"Created student {db_student.name} with ID {db_student.id}")
    return db_student

def get_students(session: Session, include_frozen: bool = False):
    query = select(Student)
    if not include_frozen:
        query = query.where(Student.is_frozen == False)
    return session.scalars(query).all()

def get_student_by_id(session: Session, student_id: int):
    return session.get(Student, student_id)

def update_student(session: Session, student_id: int, data: dict):
    student = session.get(Student, student_id)
    if not student:
        return None

    tag_names = data.pop("tags", None)

    for key, value in data.items():
        setattr(student, key, value)

    if tag_names is not None:
        existing_tags = session.query(Tag).filter(Tag.name.in_(tag_names)).all()
        existing_tag_names = {tag.name for tag in existing_tags}
        new_tags = [Tag(name=tag) for tag in tag_names if tag not in existing_tag_names]
        session.add_all(new_tags)
        session.flush()
        student.tags = existing_tags + new_tags

    session.commit()
    session.refresh(student)
    log_change(session, "UPDATE_STUDENT", f"Student ID {student_id} updated")
    return student

# ----------------------------
# Freeze / Unfreeze
# ----------------------------

def freeze_student(session: Session, student_id: int):
    student = session.get(Student, student_id)
    if student:
        student.is_frozen = True
        session.commit()
        session.refresh(student)
        log_change(session, "FREEZE_STUDENT", f"Student ID {student_id} has been frozen")
    return student

def unfreeze_student(session: Session, student_id: int):
    student = session.get(Student, student_id)
    if student:
        student.is_frozen = False
        session.commit()
        session.refresh(student)
        log_change(session, "UNFREEZE_STUDENT", f"Student ID {student_id} has been unfrozen")
    return student

# ----------------------------
# Attendance
# ----------------------------

def mark_attendance(session: Session, student_id: int, checkin_time: datetime):
    today = checkin_time.date()
    if checkin_time > datetime.now():
        raise ValueError("Check-in time cannot be in the future.")

    existing = session.execute(
        select(Attendance).where(
            and_(
                Attendance.student_id == student_id,
                Attendance.date == today,
                Attendance.checkin_time != None
            )
        )
    ).scalars().first()

    if existing:
        raise ValueError("Student already checked in today.")

    attendance = Attendance(
        student_id=student_id,
        date=today,
        checkin_time=checkin_time
    )
    session.add(attendance)
    session.commit()
    session.refresh(attendance)
    log_change(session, "MARK_ATTENDANCE", f"Check-in at {checkin_time.strftime('%H:%M')} for student ID {student_id}")
    return attendance

def mark_checkout(session: Session, student_id: int, checkout_time: datetime):
    today = checkout_time.date()
    if checkout_time > datetime.now():
        raise ValueError("Checkout time cannot be in the future.")

    attendance = session.execute(
        select(Attendance).where(
            and_(
                Attendance.student_id == student_id,
                Attendance.date == today,
                Attendance.checkout_time == None
            )
        ).order_by(Attendance.id.desc())
    ).scalars().first()

    if not attendance:
        raise ValueError("No active check-in found for today.")

    if checkout_time < attendance.checkin_time:
        raise ValueError("Checkout time cannot be before check-in time.")

    duration = int((checkout_time - attendance.checkin_time).total_seconds() // 60)
    attendance.checkout_time = checkout_time
    attendance.duration_minutes = max(duration, 0)

    session.commit()
    session.refresh(attendance)
    log_change(session, "MARK_CHECKOUT", f"Check-out at {checkout_time.strftime('%H:%M')} for student ID {student_id}. Duration: {attendance.duration_minutes} mins")
    return attendance

def get_attendance_by_student(session: Session, student_id: int):
    return session.scalars(
        select(Attendance).where(Attendance.student_id == student_id).order_by(Attendance.date.desc())
    ).all()

def get_attendance_by_date(session: Session, target_date: date):
    return session.scalars(select(Attendance).where(Attendance.date == target_date)).all()

def get_all_attendance(session: Session):
    return session.scalars(select(Attendance)).all()

def get_attendance_range(session: Session, start_date: date, end_date: date):
    return session.scalars(
        select(Attendance).where(
            and_(
                Attendance.date >= start_date,
                Attendance.date <= end_date
            )
        ).order_by(Attendance.date)
    ).all()

def get_student_attendance_summary(session: Session, student_id: int):
    records = session.scalars(select(Attendance).where(Attendance.student_id == student_id)).all()
    total_present = len(records)
    total_minutes = sum(a.duration_minutes or 0 for a in records)
    avg_minutes = total_minutes / total_present if total_present else 0
    return {
        "total_present": total_present,
        "avg_duration": round(avg_minutes, 1)
    }

# ----------------------------
# To-Do CRUD
# ----------------------------

def add_todo(session: Session, todo_data: ToDoItemCreate):
    todo = ToDoItem(**todo_data.model_dump())
    session.add(todo)
    session.commit()
    session.refresh(todo)
    log_change(session, "ADD_TODO", f"Task '{todo.task}' added for student ID {todo.student_id}")
    return todo

def get_todos(session: Session, student_id: Optional[int] = None) -> List[ToDoItem]:
    query = select(ToDoItem)
    if student_id:
        query = query.where(ToDoItem.student_id == student_id)
    return session.scalars(query.order_by(ToDoItem.order_index)).all()

def mark_todo_done(session: Session, todo_id: int):
    todo = session.get(ToDoItem, todo_id)
    if todo:
        todo.is_done = True
        session.commit()
        session.refresh(todo)
        log_change(session, "TODO_DONE", f"To-Do ID {todo_id} marked as done")
    return todo

def update_todo(session: Session, todo_id: int, data: dict):
    todo = session.get(ToDoItem, todo_id)
    if not todo:
        return None
    for key, value in data.items():
        setattr(todo, key, value)
    session.commit()
    session.refresh(todo)
    log_change(session, "TODO_UPDATED", f"To-Do ID {todo_id} updated")
    return todo

def delete_todo(session: Session, todo_id: int):
    todo = session.get(ToDoItem, todo_id)
    if todo:
        session.delete(todo)
        session.commit()
        log_change(session, "TODO_DELETED", f"To-Do ID {todo_id} deleted")
    return todo

def update_todo_order(session: Session, todo_ids_ordered: List[int]):
    for index, todo_id in enumerate(todo_ids_ordered):
        todo = session.get(ToDoItem, todo_id)
        if todo:
            todo.order_index = index
    session.commit()
    log_change(session, "TODO_REORDERED", f"Tasks reordered: {todo_ids_ordered}")
    return True

# ----------------------------
# Fee Summary
# ----------------------------

def get_fee_summary(session: Session, student_id: int):
    records = session.scalars(select(FeeRecord).where(FeeRecord.student_id == student_id)).all()
    total = sum(f.amount_paid for f in records)
    paid = total  # Assuming all FeeRecord entries are paid amounts
    due = 0.0  # Detailed due logic can be added if needed
    return {"total": total, "paid": paid, "due": due}

# ----------------------------
# Test Scores
# ----------------------------

def get_test_scores_for_student(session: Session, student_id: int):
    scores = session.scalars(select(TestScore).where(TestScore.student_id == student_id)).all()
    return [{"subject": s.subject, "score": s.score, "date": s.date} for s in scores]

# ----------------------------
# Audit Logs
# ----------------------------

def log_change(session: Session, action: str, details: str):
    india_time = datetime.now(timezone("Asia/Kolkata"))
    log = AuditLog(action=action, details=details, timestamp=india_time)
    session.add(log)
    session.commit()

def get_audit_logs(session: Session):
    return session.scalars(select(AuditLog)).all()

# ----------------------------
# Exit / Reactivate Student
# ----------------------------

def exit_student(session: Session, student_id: int, reason: str = None):
    student = session.get(Student, student_id)
    if not student:
        return None
    student.is_active = False
    student.exit_reason = reason
    session.commit()
    session.refresh(student)
    log_change(session, "EXIT_STUDENT", f"Student ID {student_id} exited. Reason: {reason or 'Not specified'}")
    return student

def reactivate_student(session: Session, student_id: int):
    student = session.get(Student, student_id)
    if not student:
        return None
    student.is_active = True
    student.reactivated_on = date.today()
    session.commit()
    session.refresh(student)
    log_change(session, "REACTIVATE_STUDENT", f"Student ID {student_id} reactivated")
    return student

# ----------------------------
# 💰 Fees & Payments CRUD
# ----------------------------

def set_fee_config(session: Session, config: StudentFeeConfigCreate):
    existing = session.query(StudentFeeConfig).filter_by(student_id=config.student_id).first()
    if existing:
        existing.monthly_fee = config.monthly_fee
        existing.note = config.note
        session.commit()
        session.refresh(existing)
        log_change(session, "UPDATE_FEE_CONFIG", f"Updated fee config for student ID {config.student_id}")
        return existing
    new_config = StudentFeeConfig(
        student_id=config.student_id,
        monthly_fee=config.monthly_fee,
        note=config.note
    )
    session.add(new_config)
    session.commit()
    session.refresh(new_config)
    log_change(session, "SET_FEE_CONFIG", f"Set fee config for student ID {config.student_id}")
    return new_config

def get_fee_config(session: Session, student_id: int):
    return session.query(StudentFeeConfig).filter_by(student_id=student_id).first()

def add_fee_payment(session: Session, payment: FeeRecordCreate):
    fee = FeeRecord(
        student_id=payment.student_id,
        amount_paid=payment.amount_paid,
        payment_date=payment.payment_date or date.today(),
        method=payment.method,
        note=payment.note,
        receipt_number=payment.receipt_number
    )
    session.add(fee)
    session.commit()
    session.refresh(fee)
    log_change(session, "FEE_PAYMENT", f"Payment of ₹{fee.amount_paid} recorded for student ID {fee.student_id}")
    return fee

def get_fee_records_for_student(session: Session, student_id: int):
    return session.scalars(
        select(FeeRecord).where(FeeRecord.student_id == student_id).order_by(FeeRecord.payment_date.desc())
    ).all()

def get_class_wise_dues(session: Session, class_level: str):
    students = session.query(Student).filter_by(class_level=class_level, is_frozen=False).all()
    report = []
    for student in students:
        config = get_fee_config(session, student.id)
        if config:
            paid = sum([f.amount_paid for f in student.fee_records])
            due = max(config.monthly_fee - paid, 0)
            report.append({
                "student_id": student.id,
                "name": student.name,
                "due_amount": due,
                "paid": paid,
                "monthly_fee": config.monthly_fee
            })
    return report

def get_monthly_collection(session: Session, year: int, month: int):
    records = session.query(FeeRecord).filter(
        extract('year', FeeRecord.payment_date) == year,
        extract('month', FeeRecord.payment_date) == month
    ).all()
    total = sum(f.amount_paid for f in records)
    return total

def get_fee_record_by_receipt(session: Session, receipt_number: str):
    return session.query(FeeRecord).filter_by(receipt_number=receipt_number).first()

def get_all_fee_records(session: Session):
    return session.scalars(select(FeeRecord).order_by(FeeRecord.payment_date.desc())).all()

# ----------------------------
# 🔄 Due Reminder Logic
# ----------------------------

def get_due_reminders(session: Session):
    today = date.today()
    cutoff_date = today - timedelta(days=30)

    students = session.query(Student).filter(Student.is_active == True, Student.is_frozen == False).all()
    reminders = []

    for student in students:
        last_payment = session.query(FeeRecord).filter_by(student_id=student.id).order_by(FeeRecord.payment_date.desc()).first()
        if not last_payment or last_payment.payment_date < cutoff_date:
            config = session.query(StudentFeeConfig).filter_by(student_id=student.id).first()
            reminders.append({
                "student_id": student.id,
                "name": student.name,
                "last_paid": last_payment.payment_date if last_payment else None,
                "due_amount": config.monthly_fee if config else None
            })
    return reminders

# ----------------------------
# 🧠 Predictive Fee Insights
# ----------------------------

def predict_next_month_collection(session: Session, year: int, month: int):
    records = session.query(FeeRecord).filter(
        extract('year', FeeRecord.payment_date) == year,
        extract('month', FeeRecord.payment_date) == month
    ).all()
    total = sum(r.amount_paid for r in records)
    prediction = round(total * 1.05, 2)  # Simple +5% growth assumption
    return {
        "actual_collected": total,
        "predicted_next_month": prediction
    }

# ----------------------------
# 🧪 Test Scores & Performance
# ----------------------------

def create_test_score(session: Session, student_id: int, subject: str, score: float, date_taken: date = None, remarks: str = ""):
    test_score = TestScore(
        student_id=student_id,
        subject=subject,
        score=score,
        date=date_taken or date.today(),
        remarks=remarks
    )
    session.add(test_score)
    session.commit()
    session.refresh(test_score)
    log_change(session, "CREATE_TEST_SCORE", f"Score {score} recorded for {subject} - Student ID {student_id}")
    return test_score

def get_test_scores_for_student(session: Session, student_id: int):
    return session.scalars(
        select(TestScore).where(TestScore.student_id == student_id).order_by(TestScore.date.desc())
    ).all()

def get_subject_performance_summary(session: Session, student_id: int):
    results = session.query(
        TestScore.subject,
        func.count(TestScore.id),
        func.avg(TestScore.score)
    ).filter(TestScore.student_id == student_id).group_by(TestScore.subject).all()

    return [
        {
            "subject": subject,
            "tests_taken": count,
            "average_score": round(avg, 1)
        } for subject, count, avg in results
    ]

def get_weak_subjects(session: Session, student_id: int, threshold: float = 40.0):
    results = session.query(
        TestScore.subject,
        func.avg(TestScore.score).label("avg_score")
    ).filter(TestScore.student_id == student_id).group_by(TestScore.subject).having(func.avg(TestScore.score) < threshold).all()

    return [{"subject": subject, "average_score": round(avg, 1)} for subject, avg in results]

def delete_test_score(session: Session, score_id: int):
    score = session.get(TestScore, score_id)
    if score:
        session.delete(score)
        session.commit()
        log_change(session, "DELETE_TEST_SCORE", f"Deleted test score ID {score_id}")
        return True
    return False

def update_test_score(session: Session, score_id: int, data: dict):
    score = session.get(TestScore, score_id)
    if not score:
        return None
    for key, value in data.items():
        setattr(score, key, value)
    session.commit()
    session.refresh(score)
    log_change(session, "UPDATE_TEST_SCORE", f"Updated test score ID {score_id}")
    return score

def export_scores_by_class(session: Session, class_level: str):
    students = session.query(Student).filter_by(class_level=class_level).all()
    output = []

    for student in students:
        scores = session.query(TestScore).filter_by(student_id=student.id).all()
        for s in scores:
            output.append({
                "student_id": student.id,
                "name": student.name,
                "subject": s.subject,
                "score": s.score,
                "date": s.date.strftime("%Y-%m-%d"),
                "remarks": s.remarks
            })
    return output

