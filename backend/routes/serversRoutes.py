# backend/routes/serversRoutes.py
import time
import os
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import docker
from pydantic import BaseModel
from typing import Dict
from celery import Celery

# Custom
from auth import get_current_user_id
from database import User, IncidentReport
from dependencies import get_db, manager
from schemas import SidecarMetrics, GameDeploymentPayload, ValheimConfigValidator, LogPayload

router = APIRouter(prefix="/servers", tags=["Servers"])

# --- Lightweight Celery Sender ---
REDIS_URL = os.getenv("REDIS_URL", "redis://redis-broker:6379/0")
celery_sender = Celery("manager_api", broker=REDIS_URL)

live_stats_cache: Dict[str, dict] = {}

# --- AI Log Buffering State ---
# Stores the last 50 lines of logs per server: { "server_id": ["log1", "log2"] }
server_log_buffers: Dict[str, list] = {}
# Prevents spamming the AI if a server loops errors: { "server_id": 1679000000.0 }
last_ai_analysis_time: Dict[str, float] = {}

AI_COOLDOWN_SECONDS = 120 # Wait 2 minutes between AI analyses per server
MAX_BUFFER_LINES = 50     # How much context to give the AI
TRIGGER_WORDS = ["error", "exception", "failed", "timeout", "critical", "crash"]

@router.get("/{server_id}/incidents")
def get_server_incidents(server_id: str, db: Session = Depends(get_db)):
    """
    Fetches the 10 most recent AI-analyzed crashes for a specific server.
    """
    incidents = (
        db.query(IncidentReport)
        .filter(IncidentReport.server_id == server_id)
        .order_by(IncidentReport.created_at.desc())
        .limit(10)
        .all()
    )
    return incidents

@router.post("/{server_id}/logs")
async def receive_logs(server_id: str, payload: LogPayload):
    # 1. Initialize buffer for this server if it doesn't exist
    if server_id not in server_log_buffers:
        server_log_buffers[server_id] = []

    buffer = server_log_buffers[server_id]
    ai_triggered = False
    triggered_line = ""

    # 2. Process incoming logs
    for line in payload.logs:
        buffer.append(line)
        
        # Check for trigger words (case insensitive)
        line_lower = line.lower()
        if any(word in line_lower for word in TRIGGER_WORDS):
            ai_triggered = True
            triggered_line = line

    # 3. Trim the buffer to save memory (Keep only the last MAX_BUFFER_LINES)
    if len(buffer) > MAX_BUFFER_LINES:
        server_log_buffers[server_id] = buffer[-MAX_BUFFER_LINES:]

    # 4. Trigger the AI Agent (in the background so we don't block the API)
    current_time = time.time()
    last_run = last_ai_analysis_time.get(server_id, 0)

    if ai_triggered and (current_time - last_run) > AI_COOLDOWN_SECONDS:
        last_ai_analysis_time[server_id] = current_time
        
        # Snapshot the logs to send to the AI
        context_logs = list(server_log_buffers[server_id]) 
        
        # SEND TO CELERY / REDIS
        # We call the task purely by its string name, no imports required!
        celery_sender.send_task(
            "analyze_logs_with_rag", 
            args=[server_id, context_logs, triggered_line]
        )

    return {"status": "logs_received", "lines_processed": len(payload.logs)}

@router.get("")
def list_servers(user_id: str = Depends(get_current_user_id)):
    return manager.list_all_servers()

@router.get("/{server_id}")
async def get_server_details(server_id: str, user_id: str = Depends(get_current_user_id)):
    container = manager.get_container(server_id)
    if not container:
        raise HTTPException(status_code=404, detail="Server not found")

    stats = live_stats_cache.get(server_id, {"cpu": 0, "ram": 0, "players": 0})
    return {
        "id": server_id,
        "name": container.name,
        "status": "online" if container.status == "running" else "offline",
        "cpu": stats["cpu"],
        "ram": stats["ram"],
        "players": stats["players"]
    }

@router.post("/{server_id}/metrics")
async def receive_metrics(server_id: str, metrics: SidecarMetrics):
    live_stats_cache[server_id] = {
        **metrics.dict(),
        "last_updated": time.time()
    }
    return {"status": "recorded"}

@router.post("/{server_id}/power")
def power_action(
    server_id: str, 
    payload: dict, 
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    action = payload.get("action")
    container = manager.get_container(server_id)

    if not container and action == "stop":
        raise HTTPException(status_code=404, detail="Server instance not found.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User session invalid.")
    
    if action == "start":
        if user.credits <= 1.0:
            raise HTTPException(status_code=402, detail="Insufficient credits.")
        manager.start_logic(server_id)
    elif action == "stop":
        container.stop(timeout=30)
    
    return {"result": "success", "status": "processing"}

@router.post("/deploy")
async def deploy_new_server(
    payload: GameDeploymentPayload, 
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    game_id = payload.game_id
    config_data = payload.config
    
    try:
        if game_id == "valheim":
            validated_config = ValheimConfigValidator(**config_data).dict()
        else:
            validated_config = config_data # Add other game validators later
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or user.credits < 5.0:
        raise HTTPException(status_code=402, detail="Insufficient credits.")

    new_container = manager.create_server(game_id, user_id, validated_config)
    return {"status": "success", "container_id": new_container.short_id}