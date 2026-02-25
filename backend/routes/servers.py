# backend/routes/servers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user_id
from dependencies import get_db, manager, redis_client
from schemas import GameDeploymentPayload, ValheimConfigValidator
from services.server_ops import ServerService

router = APIRouter(tags=["Servers"])

# Dependency Injection Factory
def get_server_service(db: Session = Depends(get_db)):
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
async def get_server_details(
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
    payload: dict, 
    user_id: str = Depends(get_current_user_id),
    service: ServerService = Depends(get_server_service)
):
    """
    Handles Start/Stop actions with credit checks.
    """
    return service.toggle_power(user_id, server_id, payload.get("action"))

@router.post("/deploy")
async def deploy_new_server(
    payload: GameDeploymentPayload, 
    user_id: str = Depends(get_current_user_id),
    service: ServerService = Depends(get_server_service)
):
    """
    Deploys a new game server container.
    """
    # Validation Layer (Still belongs in Router or Schemas)
    game_id = payload.game_id
    config_data = payload.config
    
    try:
        if game_id == "valheim":
            # Validate specifically for Valheim
            validated_config = ValheimConfigValidator(**config_data).dict()
        else:
            validated_config = config_data 
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")
    
    # Service Layer (Business Logic)
    return service.deploy_server(user_id, game_id, validated_config)