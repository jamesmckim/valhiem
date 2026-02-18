# backend/dependencies.py
from database import SessionLocal
from manager import ServerManager

# Initialize the manager once
manager = ServerManager()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()