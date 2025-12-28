"""
Emergency Evacuation Simulation Module

Implements realistic evacuation dynamics using modified Social Force Model
with panic behavior modeling.

Based on research from:
- Helbing, D., & Molnár, P. (1995). Social force model for pedestrian dynamics
- Modified for panic scenarios with increased velocities and herding behavior

References:
- https://github.com/yuxiang-gao/PySocialForce
- https://github.com/godisreal/CrowdEgress
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import numpy as np
from datetime import datetime


class EvacuationPhase(str, Enum):
    NORMAL = "normal"
    ALERT = "alert"  # Announcement made, orderly movement
    PANIC = "panic"  # Crowd pushing, reduced rationality
    CRITICAL = "critical"  # Dangerous crushing possible


@dataclass
class EmergencyExit:
    """Emergency exit configuration"""
    exit_id: str
    name: str
    location: tuple[float, float]  # (x, y) coordinates
    width: float  # meters
    max_flow_rate: int  # persons per minute
    connects_to_zone: str
    is_accessible: bool = True
    current_flow_rate: int = 0


@dataclass
class EvacuationZone:
    """Zone evacuation state"""
    zone_id: str
    current_occupancy: int
    area_sqm: float
    nearest_exits: list[str]
    distance_to_exits: dict[str, float]  # exit_id -> meters
    evacuation_started: bool = False
    evacuated_count: int = 0
    estimated_time_remaining: int = 0  # seconds


@dataclass
class EvacuationState:
    """Complete evacuation simulation state"""
    phase: EvacuationPhase
    start_time: Optional[datetime]
    elapsed_seconds: int
    total_to_evacuate: int
    total_evacuated: int
    zones: dict[str, EvacuationZone]
    bottlenecks: list[dict]
    recommendations: list[dict]
    estimated_complete_time: int  # seconds remaining


class EvacuationSimulator:
    """
    Simulates emergency evacuation using modified Social Force Model.

    Key parameters adjusted for panic scenarios:
    - Desired velocity: 1.5 m/s (normal) → 2.5 m/s (panic)
    - Personal space: 0.5m (normal) → 0.2m (panic)
    - Herding factor: Increases with panic level
    """

    # Social Force Model parameters
    NORMAL_VELOCITY = 1.5  # m/s
    PANIC_VELOCITY = 2.5  # m/s
    NORMAL_PERSONAL_SPACE = 0.5  # m
    PANIC_PERSONAL_SPACE = 0.2  # m

    # Exit flow rates (Fruin Level of Service)
    # At LOS D (critical): ~40-50 persons/min/meter of exit width
    MAX_FLOW_PER_METER = 50  # persons/min/m

    # Bottleneck thresholds
    BOTTLENECK_DENSITY = 4.0  # persons/m² triggers bottleneck
    CRUSHING_DENSITY = 6.0  # persons/m² dangerous crushing

    def __init__(
        self,
        exits: list[EmergencyExit],
        zones: list[EvacuationZone]
    ):
        self.exits = {e.exit_id: e for e in exits}
        self.zones = {z.zone_id: z for z in zones}
        self.state: Optional[EvacuationState] = None
        self.history: list[EvacuationState] = []

    def start_evacuation(
        self,
        trigger_time: datetime,
        initial_phase: EvacuationPhase = EvacuationPhase.ALERT
    ) -> EvacuationState:
        """Initialize evacuation simulation."""
        total = sum(z.current_occupancy for z in self.zones.values())

        # Calculate initial estimates
        total_exit_capacity = sum(e.max_flow_rate for e in self.exits.values())
        estimated_time = (total / total_exit_capacity) * 60 if total_exit_capacity > 0 else 9999

        # Apply safety factor (1.5x for orderly, 2x for panic)
        safety_factor = 1.5 if initial_phase == EvacuationPhase.ALERT else 2.0
        estimated_time *= safety_factor

        self.state = EvacuationState(
            phase=initial_phase,
            start_time=trigger_time,
            elapsed_seconds=0,
            total_to_evacuate=total,
            total_evacuated=0,
            zones={zid: z for zid, z in self.zones.items()},
            bottlenecks=[],
            recommendations=self._generate_initial_recommendations(),
            estimated_complete_time=int(estimated_time)
        )

        return self.state

    def simulate_step(self, dt_seconds: int = 60) -> EvacuationState:
        """
        Simulate one time step of evacuation.

        Returns updated evacuation state with:
        - Updated zone occupancies
        - Detected bottlenecks
        - Recommendations for responders
        """
        if not self.state:
            raise ValueError("Evacuation not started. Call start_evacuation first.")

        self.state.elapsed_seconds += dt_seconds
        dt_minutes = dt_seconds / 60

        # Process each zone
        for zone_id, zone in self.state.zones.items():
            if zone.current_occupancy <= 0:
                continue

            zone.evacuation_started = True

            # Calculate evacuation rate based on phase
            velocity = (
                self.PANIC_VELOCITY if self.state.phase == EvacuationPhase.PANIC
                else self.NORMAL_VELOCITY
            )

            # Find available exits and their capacities
            zone_evacuated = 0
            for exit_id in zone.nearest_exits:
                if exit_id not in self.exits:
                    continue

                exit = self.exits[exit_id]
                if not exit.is_accessible:
                    continue

                # Calculate flow to this exit
                distance = zone.distance_to_exits.get(exit_id, 50)
                travel_time = distance / velocity  # seconds

                # Effective flow rate considering distance and congestion
                density = zone.current_occupancy / zone.area_sqm
                congestion_factor = max(0.3, 1.0 - (density / self.BOTTLENECK_DENSITY) * 0.5)

                effective_rate = exit.max_flow_rate * congestion_factor * dt_minutes
                evacuated_via_exit = min(int(effective_rate), zone.current_occupancy - zone_evacuated)

                zone_evacuated += evacuated_via_exit
                exit.current_flow_rate = int(evacuated_via_exit / dt_minutes)

            zone.current_occupancy -= zone_evacuated
            zone.evacuated_count += zone_evacuated
            self.state.total_evacuated += zone_evacuated

            # Update estimated time remaining
            if zone.current_occupancy > 0:
                remaining_exits_capacity = sum(
                    self.exits[eid].max_flow_rate
                    for eid in zone.nearest_exits
                    if eid in self.exits and self.exits[eid].is_accessible
                )
                if remaining_exits_capacity > 0:
                    zone.estimated_time_remaining = int(
                        (zone.current_occupancy / remaining_exits_capacity) * 60
                    )

        # Detect bottlenecks
        self.state.bottlenecks = self._detect_bottlenecks()

        # Update phase if needed
        self._update_phase()

        # Generate new recommendations
        self.state.recommendations = self._generate_recommendations()

        # Update overall estimate
        remaining = self.state.total_to_evacuate - self.state.total_evacuated
        if remaining > 0:
            total_capacity = sum(e.max_flow_rate for e in self.exits.values() if e.is_accessible)
            self.state.estimated_complete_time = int((remaining / max(total_capacity, 1)) * 60)

        # Store history
        self.history.append(self._copy_state())

        return self.state

    def _detect_bottlenecks(self) -> list[dict]:
        """Detect dangerous congestion points."""
        bottlenecks = []

        for zone_id, zone in self.state.zones.items():
            if zone.current_occupancy <= 0:
                continue

            density = zone.current_occupancy / zone.area_sqm

            if density >= self.CRUSHING_DENSITY:
                bottlenecks.append({
                    "zone_id": zone_id,
                    "severity": "critical",
                    "density": round(density, 2),
                    "message": f"CRUSHING RISK in {zone_id}! Density {density:.1f}/m²",
                    "action": f"Immediately open additional exits for {zone_id}"
                })
            elif density >= self.BOTTLENECK_DENSITY:
                bottlenecks.append({
                    "zone_id": zone_id,
                    "severity": "high",
                    "density": round(density, 2),
                    "message": f"Bottleneck forming at {zone_id}. Density {density:.1f}/m²",
                    "action": f"Increase exit flow from {zone_id}, consider auxiliary routes"
                })

        # Check exit congestion
        for exit_id, exit in self.exits.items():
            if exit.current_flow_rate >= exit.max_flow_rate * 0.9:
                bottlenecks.append({
                    "exit_id": exit_id,
                    "severity": "medium",
                    "flow_rate": exit.current_flow_rate,
                    "message": f"Exit {exit.name} at capacity ({exit.current_flow_rate}/min)",
                    "action": f"Open adjacent exits to relieve {exit.name}"
                })

        return bottlenecks

    def _update_phase(self):
        """Update evacuation phase based on conditions."""
        if not self.state:
            return

        # Check for critical conditions
        max_density = max(
            (z.current_occupancy / z.area_sqm for z in self.state.zones.values() if z.current_occupancy > 0),
            default=0
        )

        if max_density >= self.CRUSHING_DENSITY:
            self.state.phase = EvacuationPhase.CRITICAL
        elif max_density >= self.BOTTLENECK_DENSITY:
            self.state.phase = EvacuationPhase.PANIC
        elif self.state.phase == EvacuationPhase.CRITICAL and max_density < self.BOTTLENECK_DENSITY:
            self.state.phase = EvacuationPhase.PANIC
        elif self.state.phase == EvacuationPhase.PANIC and max_density < self.BOTTLENECK_DENSITY * 0.5:
            self.state.phase = EvacuationPhase.ALERT

    def _generate_initial_recommendations(self) -> list[dict]:
        """Generate initial evacuation recommendations."""
        recs = []

        # Find highest occupancy zones
        sorted_zones = sorted(
            self.state.zones.values(),
            key=lambda z: z.current_occupancy,
            reverse=True
        )

        for i, zone in enumerate(sorted_zones[:3]):
            if zone.current_occupancy > 0:
                exits = [self.exits[eid].name for eid in zone.nearest_exits if eid in self.exits]
                recs.append({
                    "priority": i + 1,
                    "zone_id": zone.zone_id,
                    "action": f"Begin evacuation of {zone.zone_id} ({zone.current_occupancy:,} people)",
                    "exits": exits,
                    "type": "evacuation_start"
                })

        return recs

    def _generate_recommendations(self) -> list[dict]:
        """Generate dynamic recommendations during evacuation."""
        recs = []

        # Priority 1: Address bottlenecks
        for bn in self.state.bottlenecks:
            if bn.get("severity") == "critical":
                recs.append({
                    "priority": 1,
                    "action": bn["action"],
                    "type": "critical",
                    "target": bn.get("zone_id") or bn.get("exit_id")
                })

        # Priority 2: Optimize flow
        blocked_exits = [e for e in self.exits.values() if not e.is_accessible]
        if blocked_exits:
            for exit in blocked_exits:
                recs.append({
                    "priority": 2,
                    "action": f"Clear obstruction at {exit.name} to increase evacuation capacity",
                    "type": "obstruction",
                    "exit_id": exit.exit_id
                })

        # Priority 3: Progress updates
        progress = (self.state.total_evacuated / max(self.state.total_to_evacuate, 1)) * 100
        remaining_mins = self.state.estimated_complete_time / 60

        recs.append({
            "priority": 3,
            "action": f"Evacuation {progress:.0f}% complete. Estimated {remaining_mins:.0f} minutes remaining.",
            "type": "progress",
            "progress_percent": round(progress, 1)
        })

        return recs

    def _copy_state(self) -> EvacuationState:
        """Create a copy of current state for history."""
        return EvacuationState(
            phase=self.state.phase,
            start_time=self.state.start_time,
            elapsed_seconds=self.state.elapsed_seconds,
            total_to_evacuate=self.state.total_to_evacuate,
            total_evacuated=self.state.total_evacuated,
            zones={
                zid: EvacuationZone(
                    zone_id=z.zone_id,
                    current_occupancy=z.current_occupancy,
                    area_sqm=z.area_sqm,
                    nearest_exits=z.nearest_exits.copy(),
                    distance_to_exits=z.distance_to_exits.copy(),
                    evacuation_started=z.evacuation_started,
                    evacuated_count=z.evacuated_count,
                    estimated_time_remaining=z.estimated_time_remaining
                )
                for zid, z in self.state.zones.items()
            },
            bottlenecks=self.state.bottlenecks.copy(),
            recommendations=self.state.recommendations.copy(),
            estimated_complete_time=self.state.estimated_complete_time
        )

    def get_evacuation_summary(self) -> dict:
        """Get summary of evacuation for reporting."""
        if not self.state:
            return {}

        zones_cleared = sum(
            1 for z in self.state.zones.values()
            if z.current_occupancy == 0 and z.evacuated_count > 0
        )
        zones_total = len([z for z in self.state.zones.values() if z.evacuated_count > 0 or z.current_occupancy > 0])

        return {
            "status": "complete" if self.state.total_evacuated >= self.state.total_to_evacuate else "in_progress",
            "phase": self.state.phase.value,
            "elapsed_seconds": self.state.elapsed_seconds,
            "elapsed_minutes": round(self.state.elapsed_seconds / 60, 1),
            "total_evacuated": self.state.total_evacuated,
            "total_to_evacuate": self.state.total_to_evacuate,
            "progress_percent": round(
                (self.state.total_evacuated / max(self.state.total_to_evacuate, 1)) * 100, 1
            ),
            "zones_cleared": zones_cleared,
            "zones_total": zones_total,
            "bottlenecks_detected": len(self.state.bottlenecks),
            "estimated_remaining_minutes": round(self.state.estimated_complete_time / 60, 1),
            "recommendations": self.state.recommendations
        }


def calculate_evacuation_time(
    occupancy: int,
    exit_width_total: float,
    distance_to_exit: float,
    panic_level: float = 0.0  # 0.0 = calm, 1.0 = full panic
) -> dict:
    """
    Calculate estimated evacuation time for a zone.

    Based on Predtechenskii and Milinskii research on pedestrian flow.

    Args:
        occupancy: Number of people to evacuate
        exit_width_total: Total exit width in meters
        distance_to_exit: Average distance to exits in meters
        panic_level: 0.0 to 1.0

    Returns:
        dict with evacuation metrics
    """
    # Flow rate: ~82 persons/min/m at free flow, decreasing with density
    base_flow_rate = 82  # persons/min/m

    # Adjust for panic (panic increases speed but also causes bottlenecks)
    panic_factor = 1.0 + (panic_level * 0.3) - (panic_level * panic_level * 0.5)
    effective_flow = base_flow_rate * exit_width_total * panic_factor

    # Travel time
    velocity = 1.5 + (panic_level * 1.0)  # 1.5 to 2.5 m/s
    travel_time_seconds = distance_to_exit / velocity

    # Exit time (queuing + flow)
    exit_time_minutes = occupancy / effective_flow if effective_flow > 0 else 999

    # Total time
    total_seconds = travel_time_seconds + (exit_time_minutes * 60)

    return {
        "travel_time_seconds": round(travel_time_seconds, 1),
        "exit_time_minutes": round(exit_time_minutes, 1),
        "total_time_seconds": round(total_seconds, 1),
        "total_time_minutes": round(total_seconds / 60, 1),
        "effective_flow_rate": round(effective_flow, 1),
        "velocity_mps": round(velocity, 2)
    }
