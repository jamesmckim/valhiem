# backend/database.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

# This tells SQLite where to save the file
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- User Table ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    credits = Column(Float, default=0)

# --- Server Ownership Table ---
class Server(Base):
    __tablename__ = "servers"
    id = Column(String, primary_key=True) # The Docker container name
    owner_id = Column(Integer, ForeignKey("users.id"))
    hourly_cost = Column(Float, default=0.10) # $0.10 per hour this needs to be updated to the cost

# Create the tables in the .db file
def init_db():
    Base.metadata.create_all(bind=engine)
    
class IncidentReport(Base):
    __tablename__ = "incident_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(String, index=True)
    error_line = Column(String)
    recommendation = Column(Text)
    created_at = Column(DateTime, server_default=func.now())