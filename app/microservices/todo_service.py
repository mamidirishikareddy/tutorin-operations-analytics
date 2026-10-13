from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, schemas
from app.db import get_db

router = APIRouter(prefix="/todo", tags=["To-Do"])

# ----------------------------
# ✅ Get all To-Do Items (Optional: filter by student)
# ----------------------------
@router.get("/", response_model=List[schemas.ToDoItemOut])
def get_all_todos(student_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Get all to-do items, optionally filtered by student ID.
    """
    return crud.get_todos(db, student_id)

# ----------------------------
# Add a new To-Do Item
# ----------------------------
@router.post("/", response_model=schemas.ToDoItemOut)
def add_todo_item(data: schemas.ToDoItemCreate, db: Session = Depends(get_db)):
    """
    Add a new to-do/homework item for a student.
    """
    student = crud.get_student_by_id(db, data.student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with ID {data.student_id} not found.")
    
    return crud.add_todo(db, data)

# ----------------------------
# Get To-Do Items for a Specific Student
# ----------------------------
@router.get("/student/{student_id}", response_model=List[schemas.ToDoItemOut])
def get_todos(student_id: int, db: Session = Depends(get_db)):
    """
    Get all to-do tasks assigned to a specific student.
    """
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with ID {student_id} not found.")
    
    return crud.get_todos(db, student_id)

# ----------------------------
# Mark a To-Do Item as Done
# ----------------------------
@router.post("/done/{todo_id}", response_model=schemas.ToDoItemOut)
def mark_done(todo_id: int, db: Session = Depends(get_db)):
    """
    Mark a specific to-do task as completed.
    """
    todo = crud.mark_todo_done(db, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail=f"To-Do item with ID {todo_id} not found.")
    
    return todo
