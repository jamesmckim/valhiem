# sidecar/main.py
import os, time, docker, requests
from probes import get_probe

# Config from Env
TARGET = os.getenv('TARGET_CONTAINER_NAME')
GAME_TYPE = os.getenv('GAME_TYPE', 'generic')
API_URL = os.getenv('MANAGER_API_URL')
THRESHOLD = int(os.getenv('IDLE_THRESHOLD', 900)) # 15 mins

client = docker.from_env()
probe = get_probe(GAME_TYPE)
idle_seconds = 0

while True:
    try:
        # 1. Collect Resource Metrics
        container = client.containers.get(TARGET)
        stats = container.stats(stream=False)
        # Calculate CPU % logic goes here...
        stats = container.stats(stream=False)

        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]

        if system_delta > 0 and cpu_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"]) * 100.0
        else:
            cpu_percent = 0.0
        
        
        # 2. Check Player Activity
        players = probe.get_players()
        
        # 3. Handle Scaling Down
        if players == 0:
            idle_seconds += 30
        else:
            idle_seconds = 0
            
        if idle_seconds >= THRESHOLD:
            print(f"Idle threshold met. Requesting shutdown for {TARGET}...")
            requests.post(f"{API_URL}/servers/{TARGET}/stop")
            break # Exit sidecar after stopping

        # 4. Report stats to your Manager API
        # This is what your WebUI Dashboard will display!
        requests.post(f"{API_URL}/servers/{TARGET}/metrics", json={
            "cpu": 15.5, # Placeholder
            "ram": 45.2, # Placeholder
            "players": players
        })

    except Exception as e:
        print(f"Error in sidecar: {e}")

    time.sleep(30)