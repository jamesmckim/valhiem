# sidecar/main.py
import os
import time
import json
import urllib.request
import urllib.error
from probes import get_probe

# Config from Env
TARGET = os.getenv('TARGET_CONTAINER_NAME')
GAME_TYPE = os.getenv('GAME_TYPE', 'generic')
API_URL = os.getenv('MANAGER_API_URL')
THRESHOLD = int(os.getenv('IDLE_THRESHOLD_MINUTES', 15)) * 60 # 15 mins
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', '/config/server.log')

probe = get_probe(GAME_TYPE)
idle_seconds = 0

sleep_secs = 10 # amount of secounds to sleep

def send_request(endpoint, payload=None):
    """Helper to send JSON POST requests using only the standard library."""
    url = f"{API_URL}/servers/{TARGET}/{endpoint}"
    try:
        if payload:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/json')
        else:
            # Empty POST for stop command
            req = urllib.request.Request(url, method='POST')
            
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        print(f"Failed to contact manager at {endpoint}: {e}")

try:
    log_file = open(LOG_FILE_PATH, 'r')
    log_file.seek(0, os.SEEK_END)
except FileNotFoundError:
    log_file = None
    print(f"Warning: Log file {LOG_FILE_PATH} not found yet. Will keep trying.")

while True:
    try:
        # 1. Check Player Activity
        try:
            players = probe.get_player_count()
        except Exception:
            players = 0
        
        # 2. Handle Scaling Down
        if players == 0:
            idle_seconds += sleep_secs
        else:
            idle_seconds = 0
            
        if idle_seconds >= THRESHOLD:
            print(f"Idle threshold met. Requesting shutdown for {TARGET}...")
            send_request("stop")
            break # Exit sidecar after stopping

        # 3. Report stats to your Manager API
        send_request("metrics", {"players": players})
        
        # 4. Tail Logs and send to AI/Manager API
        if log_file:
            new_logs = []
            while True:
                line = log_file.readline()
                if not line:
                    break
                # Basic onise filtering before sending over the network
                clean_line = line.strip()
                if clean_line:
                    new_logs.append(clean_line)
            if new_logs:
                # Push the chunck of new logs to the manager
                send_request("logs", {"logs": new_logs})
        else:
            # Try to hook the log file again if the game server created it late
            try:
                log_file = open(LOG_FILE_PATH, 'r')
                log_file.seek(0, os.SEEK_END)
            except FileNotFoundError:
                pass

    except Exception as e:
        print(f"Error in sidecar: {e}")

    time.sleep(sleep_secs)