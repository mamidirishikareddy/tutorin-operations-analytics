from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.db import get_db
from app import models

router = APIRouter(prefix="/test-scores", tags=["Tests & Performance"])

# -------------------------------------------------------------------
# 🧪 FASTAPI ROUTES (API for test scores)
# -------------------------------------------------------------------

@router.post("/{student_id}/add")
def add_test_score_api(student_id: int, subject: str, score: float, db: Session = Depends(get_db)):
    student = db.get(models.Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    test = models.TestScore(
        student_id=student_id,
        subject=subject,
        score=score,
        date=date.today()
    )
    db.add(test)
    db.commit()
    return {"message": "Test score added successfully."}


@router.get("/{student_id}/scores")
def get_test_scores_by_student(student_id: int, db: Session = Depends(get_db)):
    scores = db.query(models.TestScore).filter(models.TestScore.student_id == student_id).all()
    return [
        {
            "subject": s.subject,
            "score": s.score,
            "date": s.date.strftime("%Y-%m-%d") if s.date else None
        }
        for s in scores
    ]


@router.get("/", response_model=List[dict])
def get_all_test_scores(db: Session = Depends(get_db)):
    scores = db.query(models.TestScore).all()
    return [
        {
            "student_id": s.student_id,
            "subject": s.subject,
            "score": s.score,
            "date": s.date.strftime("%Y-%m-%d") if s.date else None
        }
        for s in scores
    ]

# -------------------------------------------------------------------
# 🖥️ FUNCTIONS FOR STREAMLIT (no Depends)
# -------------------------------------------------------------------

def get_test_scores(student_id: int) -> List[dict]:
    db = next(get_db())
    scores = db.query(models.TestScore).filter(models.TestScore.student_id == student_id).all()
    return [
        {
            "subject": s.subject,
            "score": s.score,
            "date": s.date.strftime("%Y-%m-%d") if s.date else None
        }
        for s in scores
    ]


def add_test_score(student_id: int, subject: str, score: float) -> dict:
    db = next(get_db())
    student = db.get(models.Student, student_id)
    if not student:
        raise ValueError("Student not found")

    new_score = models.TestScore(
        student_id=student_id,
        subject=subject,
        score=score,
        date=date.today()
    )
    db.add(new_score)
    db.commit()
    db.refresh(new_score)
    return {"message": "Test score added successfully."}
