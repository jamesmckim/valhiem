# backend/manager.py
import docker
import os
import subprocess
import uuid

from dotenv import load_dotenv

load_dotenv()

# --- 1. THE MANAGER (The "Cloud-Ready" Brain) ---
class ServerManager:
    def __init__(self):
        self.uri = os.getenv("DOCKER_URL", "unix://var/run/docker.sock")
        try:
            self.client = docker.DockerClient(base_url=self.uri)
        except Exception as e:
            print(f"Docker Connection Error: {e}")

    def list_all_servers(self):
        containers = self.client.containers.list(all=True)
        server_list = []
        
        for c in containers:
            # Check for a specific label or your GAME_ID naming convention
            # For now, let's include anything that isn't the 'dashboard' or 'manager-api'
            if c.labels.get("craftcloud.role") != "game_server":
                continue
            
            server_list.append({
                "id": c.name,
                "name": c.name.replace("-", " ").title(),
                "status": "online" if c.status == "running" else "offline",
                # Include default 0s so the UI doesn't break before the sidecar reports
                "cpu": 0,
                "ram": 0,
                "players": 0
            })
        return server_list

    def get_container(self, server_id: str):
        try:
            return self.client.containers.get(server_id)
        except:
            return None
    
    def stop_server(self, server_id):
        container = self.get_container(server_id)
        if container:
            container.stop(timeout=30)
    
    def start_logic(self, server_id: str):
        # Dynamically bring up the specific service from compose
        current_env = os.environ.copy()
        subprocess.run([
            "docker-compose",
            "-f", "/app/docker-compose.yml",
            "--profile", "manual",
            "up", "-d", server_id
        ], check=True)

    def create_server(self, game_id: str, user_id: str, config_data: dict = None):
        if config_data is None:
            config_data = {}
        
        """
        Launches a new game server using Docker Compose profiles.
        """
        # Mapping frontend IDs to Compose service names
        game_map = {
            "valheim": "valheim-server",
            "minecraft": "minecraft-server",
            "rust": "rust-server",
            "palworld": "palworld-server"
        }

        service_name = game_map.get(game_id)
        if not service_name:
            raise Exception(f"Game template '{game_id}' not found in configuration.")
        
        unique_suffix = str(uuid.uuid4())[:8]
        project_name = f"craftcloud-{game_id}-{unique_suffix}"
        
        deploy_env = os.environ.copy()
        deploy_env["GAME_ID"] = project_name
        deploy_env["GAME_TYPE"] = game_id
        
        for key, value in config_data.items():
            deploy_env[key] = str(value)
        
        try:
            # Start the game server FIRST
            subprocess.run([
                "docker-compose",
                "-p", project_name,
                "-f", "/app/docker-compose.yml",
                "up", "-d", service_name
            ], env=deploy_env, check=True)
            
            # Start the sidecar SECOND
            subprocess.run([
                "docker-compose",
                "-p", project_name,
                "-f", "/app/docker-compose.yml",
                "up", "-d", "sidecar-monitor"
            ], env=deploy_env, check=True) # <-- Passed here as well
            
            # Return the container object so the API can get the ID
            return self.get_container(project_name)
            
        except subprocess.CalledProcessError as e:
            print(f"Compose Deployment Error: {e}")
            raise Exception("Failed to execute docker-compose deployment.")