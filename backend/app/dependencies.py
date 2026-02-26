# /backend/app/dependencies.py
from fastapi import Depends
from sqlalchemy.orm import Session
from redis import Redis
from celery import Celery
import os

# Import your database session factory
from database import get_db 

# Import the new components
from manager import ServerManager
from repositories.user_repo import UserRepository
from repositories.incident_repo import IncidentRepository
from services.server_service import ServerService
from services.incident_service import IncidentService
from services.telemetry_service import TelemetryService

# --- Configuration ---
# We standardize the connection details here so both Redis and Celery use the same config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_URL = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")

# Global Singletons (Initialized once)
# In a real app, you might want to initialize these in a lifespan event or strictly inside the dependency
_server_manager = ServerManager()
_redis_client = Redis(
    host=os.REDIS_HOST,
    port=int(REDIS_PORT),
    db=0,
    decode_responses=True # Helper to get strings back instead of bytes
)

_cerelry_sender = Celery("manager_api", broker=REDIS_URL)

def get_server_manager() -> ServerManager:
    return _server_manager

def get_redis() -> Redis:
    return _redis_client

def get_celery_sender() -> Celery:
    return _celery_sender

def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_incident_repo(db: Session = Depends(get_db)) -> IncidentRepository:
    return IncidentRepository(db)

def get_server_service(
    user_repo: UserRepository = Depends(get_user_repo),
    manager: ServerManager = Depends(get_server_manager),
    redis: Redis = Depends(get_redis)
) -> ServerService:
    """
    Injects the Repo, Manager, and Redis into the Service.
    This is what your Router/Controller will depend on.
    """
    return ServerService(user_repo=user_repo, manager=manager, redis=redis)

def get_incident_service(
    incident_repo: IncidentRepository = Depends(get_incident_repo),
    celery: Celery = Depends(get_celery_sender)
) -> IncidentService:
    return IncidentService(incident_repo=incident_repo, celery_app=celery)

def get_telemetry_service(
    redis: Redis = Depends(get_redis),
    celery: Celery = Depends(get_celery_sender)
) -> TelemetryService:
    return TelemetryService(redis_client=redis, celery_app=celery)