"""Simulation API routes."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.models.crowd import CrowdState, SimulationState, SimulationConfig
from app.models.venue import Venue
from app.engine.simulation import CrowdSimulationEngine, generate_arrival_curve
from app.engine.risk_analyzer import RiskAnalyzer
from app.engine.recommender import RecommendationEngine
from app.data.loader import load_venue
from app.scenarios import SCENARIOS
from app.services.data_store import data_store

router = APIRouter(prefix="/simulation", tags=["simulation"])

# Simulation state storage
_simulations: dict[str, SimulationState] = {}
_engines: dict[str, CrowdSimulationEngine] = {}
_arrival_curves: dict[str, list[tuple[float, float]]] = {}


class SimulationStartRequest(BaseModel):
    event_id: str
    scenario_id: Optional[str] = None
    speed: float = 1.0


class SimulationStepRequest(BaseModel):
    steps: int = 1


@router.post("/start")
async def start_simulation(request: SimulationStartRequest):
    """Start a new simulation for an event."""
    scenario_id = request.scenario_id or request.event_id

    # Try demo scenarios first, then custom scenarios
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        # Check for custom scenario (try with and without 'custom-' prefix)
        custom = data_store.get_custom_scenario(scenario_id)
        if not custom:
            custom = data_store.get_custom_scenario(scenario_id.replace("custom-", ""))
        if custom:
            scenario = custom
        else:
            raise HTTPException(status_code=404, detail="Scenario not found")

    venue = load_venue(scenario["venue_id"])
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    event_data = scenario["event"]

    # Initialize engine
    engine = CrowdSimulationEngine()

    # Generate arrival curve
    gates_open = datetime.fromisoformat(event_data.get("gates_open", event_data["start_time"]))
    event_start = datetime.fromisoformat(event_data["start_time"])
    pattern = scenario.get("simulation_config", {}).get("arrival_pattern", "normal")

    arrival_curve = generate_arrival_curve(
        total_attendees=event_data["expected_attendance"],
        gates_open=gates_open,
        event_start=event_start,
        pattern=pattern
    )

    # Initialize crowd state
    crowd_state = engine.initialize_state(
        venue=venue,
        event_id=scenario_id,
        expected_attendance=event_data["expected_attendance"],
        start_time=gates_open
    )

    # Handle initial occupancy for exit scenarios
    initial_occupancy = scenario.get("simulation_config", {}).get("initial_occupancy", {})
    for zone_id, count in initial_occupancy.items():
        if zone_id in crowd_state.zone_states:
            crowd_state.zone_states[zone_id].current_occupancy = count
            crowd_state.total_inside += count
            crowd_state.total_approaching -= count

    # Create simulation state - use scenario_id as key
    sim_state = SimulationState(
        event_id=scenario_id,
        is_running=True,
        speed=request.speed,
        current_time_minutes=0.0,
        crowd_state=crowd_state,
        scenario=scenario_id
    )

    _simulations[scenario_id] = sim_state
    _engines[scenario_id] = engine
    _arrival_curves[scenario_id] = arrival_curve

    return {
        "status": "started",
        "event_id": scenario_id,
        "scenario": scenario["name"],
        "venue": venue.name,
        "expected_attendance": event_data["expected_attendance"]
    }


@router.post("/step/{event_id}")
async def simulation_step(event_id: str, request: SimulationStepRequest):
    """Advance simulation by N steps."""
    if event_id not in _simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")

    sim_state = _simulations[event_id]
    engine = _engines[event_id]
    arrival_curve = _arrival_curves[event_id]

    # Get venue from scenario (check both demo and custom scenarios)
    scenario = SCENARIOS.get(sim_state.scenario)
    if not scenario:
        scenario = data_store.get_custom_scenario(sim_state.scenario)
        if not scenario:
            scenario = data_store.get_custom_scenario(sim_state.scenario.replace("custom-", ""))

    venue = load_venue(scenario["venue_id"]) if scenario else None

    if not venue:
        raise HTTPException(status_code=500, detail="Venue not found")

    # Run simulation steps
    dt_seconds = 10.0  # 10 second timesteps
    for _ in range(request.steps):
        current_minute = int(sim_state.current_time_minutes)

        # Get arrival rate for current time
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

    # Analyze risks
    risk_analyzer = RiskAnalyzer()
    alerts = risk_analyzer.analyze(venue, sim_state.crowd_state)

    # Generate recommendations
    recommender = RecommendationEngine()
    recommendations = recommender.generate(venue, sim_state.crowd_state)

    return {
        "state": sim_state,
        "alerts": alerts[:5],
        "recommendations": recommendations[:3]
    }


@router.get("/{event_id}/state")
async def get_simulation_state(event_id: str):
    """Get current simulation state."""
    if event_id not in _simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")

    sim_state = _simulations[event_id]

    # Get venue for analysis
    scenario = SCENARIOS.get(sim_state.scenario)
    venue = load_venue(scenario["venue_id"]) if scenario else None

    result = {"state": sim_state}

    if venue:
        risk_analyzer = RiskAnalyzer()
        alerts = risk_analyzer.analyze(venue, sim_state.crowd_state)
        recommender = RecommendationEngine()
        recommendations = recommender.generate(venue, sim_state.crowd_state)
        result["alerts"] = alerts[:5]
        result["recommendations"] = recommendations[:3]

    return result


@router.post("/stop/{event_id}")
async def stop_simulation(event_id: str):
    """Stop a running simulation."""
    if event_id not in _simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")

    _simulations[event_id].is_running = False
    return {"status": "stopped", "event_id": event_id}


@router.post("/reset/{event_id}")
async def reset_simulation(event_id: str):
    """Reset simulation to initial state."""
    if event_id in _simulations:
        del _simulations[event_id]
    if event_id in _engines:
        del _engines[event_id]
    if event_id in _arrival_curves:
        del _arrival_curves[event_id]

    return {"status": "reset", "event_id": event_id}


@router.get("/scenarios")
async def list_scenarios():
    """List all available scenarios (demo + custom from uploaded data)."""
    # Demo scenarios
    scenarios = [
        {
            "scenario_id": scenario_id,
            "name": scenario["name"],
            "description": scenario["description"],
            "venue_id": scenario["venue_id"],
            "event_type": scenario["event"]["event_type"],
            "expected_attendance": scenario["event"]["expected_attendance"],
            "demo_highlights": scenario.get("demo_highlights", []),
            "is_custom": False,
        }
        for scenario_id, scenario in SCENARIOS.items()
    ]

    # Custom scenarios from uploaded data
    for custom in data_store.list_custom_scenarios():
        scenarios.append({
            "scenario_id": custom["scenario_id"],
            "name": custom["name"],
            "description": custom["description"],
            "venue_id": custom["venue_id"],
            "event_type": custom["event_type"],
            "expected_attendance": custom["event"]["expected_attendance"],
            "demo_highlights": ["Custom uploaded data"],
            "is_custom": True,
        })

    return scenarios
