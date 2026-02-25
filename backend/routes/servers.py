# backend/routes/servers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user_id
from dependencies import get_db, get_server_manager, redis_client
from schemas import GameDeploymentPayload, PowerActionPayload
from services.server_ops import ServerService

from manager import ServerManager # for type checking only!!

router = APIRouter(tags=["Servers"])

# Dependency Injection Factory
def get_server_service(
    db: Session = Depends(get_db),
    manager: ServerManager = Depends(get_server_manager)
):
    return ServerService(db, manager, redis_client)

@router.get("")
def list_servers(
    user_id: str = Depends(get_current_user_id),
    service: ServerService = Depends(get_server_service)
):
    """
    Lists all available servers.
    """
    return service.list_servers()

@router.get("/{server_id}")
def get_server_details(
    server_id: str, 
    user_id: str = Depends(get_current_user_id),
    service: ServerService = Depends(get_server_service)
):
    """
    Gets details for a specific server, including live Redis stats.
    """
    return service.get_server_details(server_id)

@router.post("/{server_id}/power")
def power_action(
    server_id: str, 
    payload: PowerActionPayload, 
    user_id: str = Depends(get_current_user_id),
    service: ServerService = Depends(get_server_service)
):
    """
    Handles Start/Stop actions with credit checks.
    """
    return service.toggle_power(user_id, server_id, payload.get("action"))

@router.post("/deploy")
def deploy_new_server(
    payload: GameDeploymentPayload, 
    user_id: str = Depends(get_current_user_id),
    service: ServerService = Depends(get_server_service)
):
    """
    Deploys a new game server container.
    """
    return service.deploy_server(user_id, payload.game_id, payload.config)