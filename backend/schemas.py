# backend/schemas.py
from pydantic import BaseModel
from typing import Optional

# Metrics reported by sibling containers
class SidecarMetrics(BaseModel):
    cpu: float
    ram: float
    players: int

# Example: Future schema for deployment requests
class ServerDeploy(BaseModel):
    game_id: str
    region: Optional[str] = "us-east"

# Example: Data sent back to the user
class UserProfile(BaseModel):
    username: str
    credits: float