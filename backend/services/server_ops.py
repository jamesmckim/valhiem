# backend/services/server_ops.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from database import User
from manager import ServerManager
from redis import Redis

class ServerService:
    def __init__(self, db: Session, manager: ServerManager, redis: Redis):
        self.db = db
        self.manager = manager
        self.redis = redis

    def list_servers(self):
        """Wraps the manager's list function."""
        return self.manager.list_all_servers()

    def get_server_details(self, server_id: str):
        """Combines Docker container info with Redis stats."""
        # 1. Get static container info
        container = self.manager.get_container(server_id)
        if not container:
            # We raise the HTTP exception here so the router doesn't have to logic-check
            raise HTTPException(status_code=404, detail="Server not found")

        # 2. Fetch live stats from Redis
        stats_key = f"server_stats:{server_id}"
        stats = self.redis.hgetall(stats_key)

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

    def toggle_power(self, user_id: str, server_id: str, action: str):
        container = self.manager.get_container(server_id)
        
        # Logic check: Can't stop a server that doesn't exist
        if not container and action == "stop":
            raise HTTPException(status_code=404, detail="Server instance not found.")

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User session invalid.")
        
        if action == "start":
            # Business Logic: Check credits
            if user.credits <= 1.0:
                raise HTTPException(status_code=402, detail="Insufficient credits.")
            self.manager.start_logic(server_id)
        elif action == "stop":
            if container:
                container.stop(timeout=30)
        
        return {"result": "success", "status": "processing"}

    def deploy_server(self, user_id: str, game_id: str, config: dict):
        user = self.db.query(User).filter(User.id == user_id).first()
        
        # Business Logic: Higher credit requirement for deployment
        if not user or user.credits < 5.0:
            raise HTTPException(status_code=402, detail="Insufficient credits.")

        new_container = self.manager.create_server(game_id, user_id, config)
        return {"status": "success", "container_id": new_container.short_id}