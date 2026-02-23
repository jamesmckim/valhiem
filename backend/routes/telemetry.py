# backend/routes/telemetry.py
from fastapi import APIRouter
from schemas import LogPayload, SidecarMetrics
from dependencies import redis_client, celery_sender

router = APIRouter(tags=["Telemetry"])

# --- Constants ---
AI_COOLDOWN_SECONDS = 120
MAX_BUFFER_LINES = 50
TRIGGER_WORDS = ["error", "exception", "failed", "timeout", "critical", "crash"]
METRICS_TTL = 60

@router.post("/{server_id}/logs")
async def receive_logs(server_id: str, payload: LogPayload):
    log_key = f"server_logs:{server_id}"
    cooldown_key = f"ai_cooldown:{server_id}"
    
    ai_triggered = False
    triggered_line = ""

    if payload.logs:
        redis_client.rpush(log_key, *payload.logs)
        redis_client.ltrim(log_key, -MAX_BUFFER_LINES, -1)

        for line in payload.logs:
            if any(word in line.lower() for word in TRIGGER_WORDS):
                ai_triggered = True
                triggered_line = line
                break

    ai_task_id = None

    if ai_triggered:
        # Distributed Lock check
        can_trigger = redis_client.set(cooldown_key, "active", nx=True, ex=AI_COOLDOWN_SECONDS)
        
        if can_trigger:
            context_logs = redis_client.lrange(log_key, 0, -1)
            task = celery_sender.send_task(
                "analyze_logs_with_rag", 
                args=[server_id, context_logs, triggered_line]
            )
            ai_task_id = task.id

    return {
        "status": "logs_received", 
        "lines_processed": len(payload.logs),
        "ai_task_id": ai_task_id
    }

@router.post("/{server_id}/metrics")
async def receive_metrics(server_id: str, metrics: SidecarMetrics):
    stats_key = f"server_stats:{server_id}"
    
    redis_client.hset(stats_key, mapping=metrics.dict())
    redis_client.expire(stats_key, METRICS_TTL)
    
    return {"status": "recorded"}