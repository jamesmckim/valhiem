# backend/routes/servers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth import get_current_user_id
from database import User
from dependencies import get_db, manager, redis_client
from schemas import GameDeploymentPayload, ValheimConfigValidator

router = APIRouter(tags=["Servers"])

@router.get("")
def list_servers(user_id: str = Depends(get_current_user_id)):
    return manager.list_all_servers()

@router.get("/{server_id}")
async def get_server_details(server_id: str, user_id: str = Depends(get_current_user_id)):
    # 1. Get static container info
    container = manager.get_container(server_id)
    if not container:
        raise HTTPException(status_code=404, detail="Server not found")

    # 2. Fetch live stats from Redis
    stats_key = f"server_stats:{server_id}"
    stats = redis_client.hgetall(stats_key)

    # 3. Default to zero if no stats found
    cpu = float(stats.get("cpu", 0))
    ram = float(stats.get("ram", 0))
    players = int(stats.get("players", 0))

    return {
        "id": server_id,
        "name": container.name,
        "status": "online" if container.status == "running" else "offline",
        "cpu": cpu,
        "ram": ram,
        "players": players
    }

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
            validated_config = config_data 
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or user.credits < 5.0:
        raise HTTPException(status_code=402, detail="Insufficient credits.")

    new_container = manager.create_server(game_id, user_id, validated_config)
    return {"status": "success", "container_id": new_container.short_id}