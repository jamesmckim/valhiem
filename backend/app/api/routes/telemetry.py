# /backend/app/api/routes/telemetry.py
from fastapi import APIRouter, Depends
from schemas import LogPayload, SidecarMetrics
from services.telemetry_service import TelemetryService
from dependencies import get_telemetry_service

router = APIRouter(tags=["Telemetry"])

@router.post("/{server_id}/logs")
async def receive_logs(
    server_id: str, 
    payload: LogPayload,
    service: TelemetryService = Depends(get_telemetry_service)
):
    return service.process_logs(server_id, payload.logs)

@router.post("/{server_id}/metrics")
async def receive_metrics(
    server_id: str, 
    metrics: SidecarMetrics,
    service: TelemetryService = Depends(get_telemetry_service)
):
    return service.process_metrics(server_id, metrics)