from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from app.db import get_db
from app import models

router = APIRouter(prefix="/revision", tags=["Revision Planner"])

# ----------------------------
# 1. Create a Weekly Revision Task
# ----------------------------
@router.post("/add")
def add_revision_task(
    student_id: int,
    subject: str,
    topic: str,
    week_start: Optional[date] = None,
    notes: Optional[str] = "",
    db: Session = Depends(get_db)
):
    student = db.get(models.Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    task = models.RevisionPlanner(
        student_id=student_id,
        subject=subject,
        topic=topic,
        week_start=week_start or date.today(),
        notes=notes,
        is_done=False
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"message": "Revision task added", "task_id": task.id}

# ----------------------------
# 2. List All or Student-Specific Tasks (Latest First)
# ----------------------------
@router.get("/list")
def list_tasks(
    student_id: Optional[int] = Query(None, description="Optional student ID filter"),
    db: Session = Depends(get_db)
):
    query = db.query(models.RevisionPlanner)
    if student_id:
        query = query.filter_by(student_id=student_id)
    return query.order_by(models.RevisionPlanner.week_start.desc()).all()

# ----------------------------
# 3. Mark Task as Done
# ----------------------------
@router.put("/mark_done/{task_id}")
def mark_task_done(task_id: int, db: Session = Depends(get_db)):
    task = db.get(models.RevisionPlanner, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.is_done = True
    db.commit()
    return {"message": "Task marked as completed"}

# ----------------------------
# 4. Delete a Task
# ----------------------------
@router.delete("/delete/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(models.RevisionPlanner, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}

# ----------------------------
# 5. Get Suggestions for Revision Subjects (based on Test Scores)
# [OPTIONAL - You already use this logic in UI, but API version available]
# ----------------------------
@router.get("/suggest_subjects/{student_id}")
def suggest_weak_subjects(student_id: int, db: Session = Depends(get_db)):
    scores = db.query(models.TestScore).filter_by(student_id=student_id).all()
    if not scores:
        return []

    weak_subjects = list({
        s.subject for s in scores if s.score < 50
    })
    return {"weak_subjects": sorted(weak_subjects)}
