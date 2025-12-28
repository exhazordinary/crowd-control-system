"""
AI-Powered Crowd Control System - FastAPI Backend

Main application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import venues, events, simulation, alerts, data_import
from app.api.websocket import simulation_websocket_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("Starting Crowd Control System API...")
    yield
    # Shutdown
    print("Shutting down Crowd Control System API...")


app = FastAPI(
    title="Crowd Control System API",
    description="AI-powered crowd simulation and management for Malaysian events",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(venues.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(simulation.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(data_import.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Crowd Control System API",
        "version": "0.1.0",
        "description": "AI-powered crowd simulation for Malaysian events",
        "endpoints": {
            "venues": "/api/venues",
            "events": "/api/events",
            "simulation": "/api/simulation",
            "alerts": "/api/alerts",
            "data_import": "/api/data",
            "websocket": "/ws/simulation/{event_id}"
        },
        "features": [
            "Transport timing integration (LRT/Bus)",
            "Evacuation simulation",
            "Parking overflow prediction",
            "Restroom queue simulation",
            "CSV/JSON data import",
            "Actionable AI recommendations"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.websocket("/ws/simulation/{event_id}")
async def websocket_endpoint(websocket: WebSocket, event_id: str):
    """WebSocket endpoint for real-time simulation updates."""
    await simulation_websocket_handler(websocket, event_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
