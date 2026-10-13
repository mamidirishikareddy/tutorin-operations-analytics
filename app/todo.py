from sqlmodel import Session, select
from datetime import datetime

from app.models import ToDoItem


# ----------------------------
# Add a To-Do Task
# ----------------------------
def create_todo(session: Session, student_id: int, task: str, due_date: datetime):
    todo = ToDoItem(
        student_id=student_id,
        task=task,
        due_date=due_date,
        completed=False
    )
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


# ----------------------------
# Get To-Do Items by Student
# ----------------------------
def get_todos_for_student(session: Session, student_id: int):
    statement = select(ToDoItem).where(ToDoItem.student_id == student_id)
    return session.exec(statement).all()


# ----------------------------
# Update Task Status or Details
# ----------------------------
def update_todo(session: Session, todo_id: int, updates: dict):
    todo = session.get(ToDoItem, todo_id)
    if todo:
        for key, value in updates.items():
            setattr(todo, key, value)
        session.commit()
        session.refresh(todo)
    return todo


# ----------------------------
# Delete a To-Do Task
# ----------------------------
def delete_todo(session: Session, todo_id: int):
    todo = session.get(ToDoItem, todo_id)
    if todo:
        session.delete(todo)
        session.commit()
        return True
    return False


# ----------------------------
# Mark Task as Completed
# ----------------------------
def mark_task_complete(session: Session, todo_id: int):
    todo = session.get(ToDoItem, todo_id)
    if todo and not todo.completed:
        todo.completed = True
        session.commit()
        session.refresh(todo)
    return todo
