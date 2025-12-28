"""WebSocket handler for real-time simulation updates."""

import asyncio
import json
from datetime import datetime
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

from app.engine.risk_analyzer import RiskAnalyzer
from app.engine.recommender import RecommendationEngine
from app.data.loader import load_venue
from app.scenarios import SCENARIOS


class ConnectionManager:
    """Manage WebSocket connections for simulation updates."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, event_id: str):
        """Accept and track a new connection."""
        await websocket.accept()
        if event_id not in self.active_connections:
            self.active_connections[event_id] = []
        self.active_connections[event_id].append(websocket)

    def disconnect(self, websocket: WebSocket, event_id: str):
        """Remove a connection."""
        if event_id in self.active_connections:
            if websocket in self.active_connections[event_id]:
                self.active_connections[event_id].remove(websocket)

    async def broadcast(self, event_id: str, message: dict):
        """Broadcast message to all connections for an event."""
        if event_id not in self.active_connections:
            return

        dead_connections = []
        for connection in self.active_connections[event_id]:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        # Clean up dead connections
        for conn in dead_connections:
            self.disconnect(conn, event_id)


manager = ConnectionManager()


async def simulation_websocket_handler(websocket: WebSocket, event_id: str):
    """
    Handle WebSocket connection for real-time simulation updates.

    Messages sent to client:
    - {"type": "state_update", "data": SimulationState}
    - {"type": "alert", "data": Alert}
    - {"type": "recommendation", "data": Recommendation}

    Messages from client:
    - {"type": "set_speed", "speed": float}
    - {"type": "pause"}
    - {"type": "resume"}
    - {"type": "step", "count": int}
    """
    # Import here to avoid circular dependency
    from app.api.routes.simulation import _simulations, _engines, _arrival_curves

    await manager.connect(websocket, event_id)

    try:
        # Send initial state if simulation exists
        if event_id in _simulations:
            sim_state = _simulations[event_id]
            await websocket.send_json({
                "type": "state_update",
                "data": json.loads(sim_state.model_dump_json())
            })

        while True:
            # Wait for messages from client
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)

                if data.get("type") == "set_speed":
                    if event_id in _simulations:
                        _simulations[event_id].speed = data.get("speed", 1.0)
                        await websocket.send_json({
                            "type": "speed_changed",
                            "speed": _simulations[event_id].speed
                        })

                elif data.get("type") == "pause":
                    if event_id in _simulations:
                        _simulations[event_id].is_paused = True
                        await websocket.send_json({"type": "paused"})

                elif data.get("type") == "resume":
                    if event_id in _simulations:
                        _simulations[event_id].is_paused = False
                        await websocket.send_json({"type": "resumed"})

                elif data.get("type") == "step":
                    await _run_simulation_step(
                        websocket, event_id,
                        data.get("count", 1)
                    )

            except asyncio.TimeoutError:
                # No message received, check if we should auto-step
                if event_id in _simulations:
                    sim_state = _simulations[event_id]
                    if sim_state.is_running and not sim_state.is_paused:
                        await _run_simulation_step(websocket, event_id, 1)
                        # Delay based on speed
                        await asyncio.sleep(1.0 / sim_state.speed)

    except WebSocketDisconnect:
        manager.disconnect(websocket, event_id)


async def _run_simulation_step(websocket: WebSocket, event_id: str, steps: int = 1):
    """Run simulation steps and send updates."""
    from app.api.routes.simulation import _simulations, _engines, _arrival_curves

    if event_id not in _simulations:
        return

    sim_state = _simulations[event_id]
    engine = _engines.get(event_id)
    arrival_curve = _arrival_curves.get(event_id, [])

    if not engine:
        return

    # Get venue
    scenario = SCENARIOS.get(sim_state.scenario)
    if not scenario:
        return

    venue = load_venue(scenario["venue_id"])
    if not venue:
        return

    # Run steps
    dt_seconds = 10.0
    for _ in range(steps):
        current_minute = int(sim_state.current_time_minutes)

        # Get arrival rate
        arrival_rate = 0.0
        for minute, rate in arrival_curve:
            if minute <= current_minute < minute + 1:
                arrival_rate = rate
                break

        # Advance simulation
        sim_state.crowd_state = engine.simulate_timestep(
            venue=venue,
            state=sim_state.crowd_state,
            dt_seconds=dt_seconds,
            arrival_rate=arrival_rate
        )
        sim_state.current_time_minutes += dt_seconds / 60

    _simulations[event_id] = sim_state

    # Send state update
    await websocket.send_json({
        "type": "state_update",
        "data": json.loads(sim_state.model_dump_json())
    })

    # Analyze and send alerts
    risk_analyzer = RiskAnalyzer()
    alerts = risk_analyzer.analyze(venue, sim_state.crowd_state)
    for alert in alerts[:3]:
        await websocket.send_json({
            "type": "alert",
            "data": json.loads(alert.model_dump_json())
        })

    # Send recommendations
    recommender = RecommendationEngine()
    recommendations = recommender.generate(venue, sim_state.crowd_state)
    for rec in recommendations[:2]:
        await websocket.send_json({
            "type": "recommendation",
            "data": json.loads(rec.model_dump_json())
        })
