"""Crowd state and agent models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AgentState(str, Enum):
    APPROACHING = "approaching"
    QUEUING = "queuing"
    ENTERING = "entering"
    MOVING = "moving"
    SEATED = "seated"
    STANDING = "standing"
    EXITING = "exiting"
    EXITED = "exited"


class Agent(BaseModel):
    """Individual crowd agent for detailed simulation."""
    agent_id: str
    ticket_category: str
    arrival_time: datetime
    current_zone: Optional[str] = None
    destination_zone: str
    position: tuple[float, float] = (0.0, 0.0)
    velocity: tuple[float, float] = (0.0, 0.0)
    state: AgentState = AgentState.APPROACHING
    target_gate: Optional[str] = None


class ZoneState(BaseModel):
    """Current state of a zone."""
    zone_id: str
    current_occupancy: int
    density: float = Field(description="persons per square meter")
    inflow_rate: float = Field(default=0.0, description="persons per minute entering")
    outflow_rate: float = Field(default=0.0, description="persons per minute exiting")
    risk_level: str = "safe"  # safe, moderate, high, critical


class GateState(BaseModel):
    """Current state of a gate."""
    gate_id: str
    queue_length: int
    throughput_rate: float = Field(description="current persons per minute")
    wait_time_minutes: float
    is_congested: bool = False


class CrowdState(BaseModel):
    """Complete crowd state at a point in time."""
    event_id: str
    timestamp: datetime
    simulation_time_minutes: float = 0.0

    # Aggregate stats
    total_inside: int = 0
    total_queuing: int = 0
    total_exited: int = 0
    total_approaching: int = 0

    # Zone states
    zone_states: dict[str, ZoneState] = Field(default_factory=dict)

    # Gate states
    gate_states: dict[str, GateState] = Field(default_factory=dict)

    # Flow rates
    overall_inflow_rate: float = 0.0  # persons/minute entering venue
    overall_outflow_rate: float = 0.0  # persons/minute exiting venue

    # For agent-based simulation (optional)
    agents: list[Agent] = Field(default_factory=list)

    @property
    def average_density(self) -> float:
        """Average density across all zones."""
        if not self.zone_states:
            return 0.0
        return sum(z.density for z in self.zone_states.values()) / len(self.zone_states)

    @property
    def max_density(self) -> float:
        """Maximum density in any zone."""
        if not self.zone_states:
            return 0.0
        return max(z.density for z in self.zone_states.values())

    @property
    def critical_zones(self) -> list[str]:
        """List of zones at critical density."""
        return [z.zone_id for z in self.zone_states.values() if z.risk_level == "critical"]


class SimulationConfig(BaseModel):
    """Simulation configuration parameters."""
    event_id: str
    scenario: str = "normal"  # normal, rush, evacuation
    speed: float = Field(default=1.0, ge=0.1, le=100.0)
    start_from_minutes: float = 0.0
    use_agent_model: bool = False  # True for <5000 attendees
    timestep_seconds: float = 1.0


class SimulationState(BaseModel):
    """Complete simulation state for API responses."""
    event_id: str
    is_running: bool = False
    is_paused: bool = False
    speed: float = 1.0
    current_time_minutes: float = 0.0
    crowd_state: CrowdState
    scenario: str = "normal"
