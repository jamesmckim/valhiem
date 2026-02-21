# worker/ai_worker.py
import os
import uuid
from celery import Celery
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func

# --- Configs ---
REDIS_URL = os.getenv("REDIS_URL", "redis://redis-broker:6379/0")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant-db:6333")
DATABASE_URL = os.getenv("DATABASE_URL")
LLM_URL = os.getenv("LLM_URL", "http://host.docker.internal:1234/v1")

# Initialize the OpenAI Client to point to your local machine
client = OpenAI(
    base_url=LLM_URL, 
    api_key="dummy-key-not-checked" # Local runners require a key string, but ignore what it says
)

# --- Initialize Isolated Database Connection ---
engine = create_engine(DATABASE_URL, poolclass=NullPool)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Define the local DB Model ---
Base = declarative_base()

class IncidentReport(Base):
    __tablename__ = "incident_reports"
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(String, index=True)
    error_line = Column(String)
    recommendation = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

# --- Initialize ---
celery_app = Celery("ai_worker", broker=REDIS_URL, backend=REDIS_URL)
qdrant = QdrantClient(url=QDRANT_URL)

# --- Initialize Isolated Database Connection ---
engine = create_engine(DATABASE_URL, poolclass=NullPool)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

COLLECTION_NAME = "server_knowledge"

def get_embedding(text: str) -> list:
    """Calls OpenAI to convert text into a numeric vector array."""
    response = client.embeddings.create(
        input=text,
        model="nomic-embed-text"
    )
    return response.data[0].embedding

def setup_collection():
    if not qdrant.collection_exists(COLLECTION_NAME):
        sample_embedding = get_embedding("test")
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=len(sample_embedding), distance=Distance.COSINE),
        )

# --- THE CELERY TASK ---
@celery_app.task(name="analyze_logs_with_rag")
def analyze_logs_with_rag_task(server_id: str, log_context: list, error_line: str):
    setup_collection()
    print(f"[{server_id}] Worker pulled RAG task from Redis. Trigger: {error_line}")
    
    # 1. RETRIEVAL
    error_vector = get_embedding(error_line)
    retrieved_docs_text = "No historical documentation found."

    if error_vector:
        search_results = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=error_vector,
            limit=3
        )
        if search_results.points:
            retrieved_docs_text = "\n\n".join([hit.payload["text"] for hit in search_results])

    # 2. GENERATION
    log_text = "\n".join(log_context)
    
    # OpenAI uses a strict System/User messaging structure
    messages = [
        {
            "role": "system", 
            "content": (
                "You are an expert game server administrator. Identify the root cause of the "
                "server crash and provide a short, actionable recommendation under 3 sentences."
            )
        },
        {
            "role": "user",
            "content": f"""
            Official documentation Context:
            {retrieved_docs_text}
            
            Server logs leading up to the crash:
            {log_text}
            
            Error line detected: "{error_line}"
            """
        }
    ]

    try:
        response = client.chat.completions.create(
            model="phi3",
            messages=messages,
            temperature=0.2 # Keep it analytical and factual
        )
        
        ai_recommendation = response.choices[0].message.content.strip()
        
        # --- Save the recommendation to the database ---
        db = SessionLocal()
        try:
            new_incident = IncidentReport(
                server_id=server_id,
                error_line=error_line,
                recommendation=ai_recommendation
            )
            db.add(new_incident)
            db.commit()
            print(f"[{server_id}] Successfully saved Incident Report to DB.")
        except Exception as db_err:
            db.rollback()
            print(f"[{server_id}] Database save failed: {db_err}")
        finally:
            db.close() # Always close the session to free up the connection
            
        return ai_recommendation
            
    except Exception as e:
        print(f"[{server_id}] Worker failed to process AI request: {e}")
        
    return None