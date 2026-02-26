# backend/app/services/server_service.py
from fastapi import HTTPException, status
from redis import Redis

from manager import ServerManager
from repositories.user_repo import UserRepository
from repositories.server_repo import ServerRepository  # [New Import]
from schemas import ValheimConfigValidator

class ServerService:
    def __init__(
        self, 
        user_repo: UserRepository, 
        server_repo: ServerRepository,  # [New Dependency]
        manager: ServerManager, 
        redis: Redis
    ):
        self.user_repo = user_repo
        self.server_repo = server_repo
        self.manager = manager
        self.redis = redis

    def list_servers(self):
        """Wraps the manager's list function."""
        # Optional: You could now filter this by referencing self.server_repo if needed
        return self.manager.list_all_servers()

    def get_server_details(self, server_id: str):
        """Combines Docker container info with Redis stats."""
        # 1. Get static container info
        container = self.manager.get_container(server_id)
        if not container:
            raise HTTPException(status_code=404, detail="Server container not found")

        # 2. Fetch live stats from Redis
        stats_key = f"server_stats:{server_id}"
        stats = self.redis.hgetall(stats_key)

        # 3. Default to zero if no stats found
        cpu = float(stats.get(b"cpu", 0))
        ram = float(stats.get(b"ram", 0))
        players = int(stats.get(b"players", 0))

        return {
            "id": server_id,
            "name": container.name,
            "status": "online" if container.status == "running" else "offline",
            "cpu": cpu,
            "ram": ram,
            "players": players
        }

    def toggle_power(self, user_id: str, server_id: str, action: str):
        # 1. [New] Ownership Check: Verify server exists in DB and belongs to user
        server_record = self.server_repo.get(server_id)
        
        if not server_record:
            raise HTTPException(status_code=404, detail="Server not registered in database.")
            
        # Ensure user_id is compared correctly (assuming user_id passed is compatible with DB type)
        if str(server_record.owner_id) != str(user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this server.")

        # 2. Retrieve Docker container
        container = self.manager.get_container(server_id)
        
        # Logic check: Can't stop a server that doesn't exist
        if not container and action == "stop":
            raise HTTPException(status_code=404, detail="Server instance not found.")

        # 3. Retrieve User for credit check
        user = self.user_repo.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User session invalid.")
        
        if action == "start":
            # Business Logic: Check credits
            if user.credits <= 1.0:
                raise HTTPException(status_code=402, detail="Insufficient credits.")
            self.manager.start_logic(server_id)
        elif action == "stop":
            self.manager.stop_server(server_id)
        
        return {"result": "success", "status": "processing"}

    def deploy_server(self, user_id: str, game_id: str, config: dict):
        if game_id == "valheim":
            try:
                # Validate and sanitize using the Pydantic model
                config = ValheimConfigValidator(**config).dict()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")
        
        # 1. Verify User and Credits
        user = self.user_repo.get(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        
        if user.credits < 5.0:
            raise HTTPException(status_code=402, detail="Insufficient credits.")

        # 2. Create Docker Container
        new_container = self.manager.create_server(game_id, user_id, config)
        
        # 3. [New] Persist Server Ownership in DB
        # We use the container name/ID as the primary key for the Server table
        try:
            self.server_repo.create({
                "id": new_container.name, 
                "owner_id": user.id,
                "hourly_cost": 0.10 # Default cost
            })
        except Exception as e:
            # Rollback: If DB save fails, we should probably destroy the container 
            # to prevent 'orphan' servers, or log a critical error.
            # self.manager.delete_server(new_container.name) 
            raise HTTPException(status_code=500, detail=f"Failed to register server: {str(e)}")

        return {"status": "success", "container_id": new_container.name}