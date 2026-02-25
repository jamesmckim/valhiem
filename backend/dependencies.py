# backend/dependencies.py
import os
import redis
from celery import Celery
from database import SessionLocal
from manager import ServerManager

# --- Configuration ---
REDIS_URL = os.getenv("REDIS_URL", "redis://redis-broker:6379/0")

# Initialize the manager once
manager = ServerManager()
def get_server_manager():
    return manager

# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# --- Messaging Dependencies ---
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

celery_sender = Celery("manager_api", broker=REDIS_URL)