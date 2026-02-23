# backend/routes/incidents.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from celery.result import AsyncResult
from database import IncidentReport
from dependencies import get_db, celery_sender

router = APIRouter(tags=["Incidents"])

@router.get("/{server_id}/incidents")
def get_server_incidents(server_id: str, db: Session = Depends(get_db)):
    incidents = (
        db.query(IncidentReport)
        .filter(IncidentReport.server_id == server_id)
        .order_by(IncidentReport.created_at.desc())
        .limit(10)
        .all()
    )
    return incidents

@router.get("/{server_id}/incidents/resolve/{task_id}")
def resolve_ai_incident(server_id: str, task_id: str, db: Session = Depends(get_db)):
    result = AsyncResult(task_id, app=celery_sender)
    
    if not result.ready():
        return {"status": "pending"}
        
    data = result.result
    
    if not data or data.get("status") == "error":
        result.forget()
        return {"status": "error", "detail": data.get("error_message", "Unknown error")}
        
    new_incident = IncidentReport(
        server_id=server_id,
        error_line=data.get("error_line"),
        recommendation=data.get("recommendation")
    )
    
    try:
        db.add(new_incident)
        db.commit()
        db.refresh(new_incident)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save incident to database.")
    
    result.forget() 
    
    return {
        "status": "completed",
        "incident": new_incident
    }