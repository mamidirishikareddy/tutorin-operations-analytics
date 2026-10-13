# app/microservices/audit_service.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import crud, schemas
from app.db import get_db
from typing import List

router = APIRouter(prefix="/audit", tags=["Audit Logs"])

# ----------------------------
# Get All Audit Logs
# ----------------------------
@router.get("/", response_model=List[schemas.AuditLogOut])
def get_logs(db: Session = Depends(get_db)):
    """
    Retrieve the complete list of audit log entries.
    """
    return crud.get_audit_logs(db)
