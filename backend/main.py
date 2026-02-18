# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routes import authRoutes, serversRoutes # Import your new routers

app = FastAPI(title="CraftCloud API")

# Initialize database tables
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the routes
app.include_router(authRoutes.router)
app.include_router(serversRoutes.router)

@app.get("/")
async def root():
    return {"message": "CraftCloud API is operational"}