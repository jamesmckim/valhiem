# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routes import authRoutes, servers, telemetry, incidents # Import your new routers

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

app.include_router(servers.router, prefix="/servers")
app.include_router(telemetry.router, prefix="/servers")
app.include_router(incidents.router, prefix="/servers")

@app.get("/")
async def root():
    return {"message": "CraftCloud API is operational"}