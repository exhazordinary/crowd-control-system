"""
Hybrid Crowd Simulation Engine.

Uses flow-based simulation for large crowds (5000+) and agent-based for smaller events.
Based on Social Force Model (Helbing et al.) for pedestrian dynamics.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import truncnorm

from app.models.venue import Venue, Zone, Gate
from app.models.crowd import CrowdState, ZoneState, GateState, Agent, AgentState


@dataclass
class SimulationParams:
    """Physical parameters for crowd simulation."""
    # Walking speeds (m/s)
    desired_speed: float = 1.34
    max_speed: float = 2.5

    # Density thresholds (persons/m^2)
    density_comfortable: float = 0.5
    density_crowded: float = 2.0
    density_dangerous: float = 4.0
    density_critical: float = 6.0

    # Processing times (seconds)
    gate_scan_time: float = 3.0
    vip_scan_time: float = 1.5

    # Flow reduction factors at high density
    flow_reduction_crowded: float = 0.7
    flow_reduction_dangerous: float = 0.4
    flow_reduction_critical: float = 0.1


class CrowdSimulationEngine:
    """
    Hybrid simulation engine that scales from small to large events.

    - Agent-based for < 5000 attendees (detailed behavior)
    - Flow-based for >= 5000 attendees (aggregate patterns)
    """

    AGENT_THRESHOLD = 5000

    def __init__(self, params: SimulationParams | None = None):
        self.params = params or SimulationParams()
        self._rng = np.random.default_rng(42)

    def initialize_state(
        self,
        venue: Venue,
        event_id: str,
        expected_attendance: int,
        start_time: datetime
    ) -> CrowdState:
        """Initialize crowd state for simulation."""
        zone_states = {
            zone.zone_id: ZoneState(
                zone_id=zone.zone_id,
                current_occupancy=0,
                density=0.0,
                risk_level="safe"
            )
            for zone in venue.zones
        }

        gate_states = {
            gate.gate_id: GateState(
                gate_id=gate.gate_id,
                queue_length=0,
                throughput_rate=0.0,
                wait_time_minutes=0.0
            )
            for gate in venue.gates
        }

        return CrowdState(
            event_id=event_id,
            timestamp=start_time,
            total_approaching=expected_attendance,
            zone_states=zone_states,
            gate_states=gate_states
        )

    def simulate_timestep(
        self,
        venue: Venue,
        state: CrowdState,
        dt_seconds: float,
        arrival_rate: float
    ) -> CrowdState:
        """
        Advance simulation by one timestep.

        Args:
            venue: Venue configuration
            state: Current crowd state
            dt_seconds: Time delta in seconds
            arrival_rate: Expected arrivals per minute at this time
        """
        new_state = state.model_copy(deep=True)
        new_state.timestamp += timedelta(seconds=dt_seconds)
        new_state.simulation_time_minutes += dt_seconds / 60

        # Process arrivals to gates
        self._process_arrivals(venue, new_state, arrival_rate, dt_seconds)

        # Process gate throughput
        self._process_gates(venue, new_state, dt_seconds)

        # Process internal flow between zones
        self._process_zone_flow(venue, new_state, dt_seconds)

        # Update density and risk levels
        self._update_densities(venue, new_state)

        return new_state

    def _process_arrivals(
        self,
        venue: Venue,
        state: CrowdState,
        arrival_rate: float,
        dt_seconds: float
    ) -> None:
        """Distribute new arrivals to gate queues."""
        if state.total_approaching <= 0:
            return

        arrivals_this_step = min(
            int(arrival_rate * dt_seconds / 60 + self._rng.random()),
            state.total_approaching
        )

        if arrivals_this_step <= 0:
            return

        # Distribute to open gates based on capacity
        open_gates = [g for g in venue.gates if g.is_open and not g.is_emergency_exit]
        if not open_gates:
            return

        total_capacity = sum(g.capacity_per_minute for g in open_gates)

        for gate in open_gates:
            gate_share = gate.capacity_per_minute / total_capacity
            gate_arrivals = int(arrivals_this_step * gate_share)
            state.gate_states[gate.gate_id].queue_length += gate_arrivals
            state.total_approaching -= gate_arrivals
            state.total_queuing += gate_arrivals

    def _process_gates(self, venue: Venue, state: CrowdState, dt_seconds: float) -> None:
        """Process people through gates into venue."""
        total_entered = 0

        for gate in venue.gates:
            if not gate.is_open:
                continue

            gate_state = state.gate_states[gate.gate_id]
            if gate_state.queue_length <= 0:
                continue

            # Calculate throughput based on capacity and queue
            max_throughput = gate.capacity_per_minute * dt_seconds / 60
            actual_throughput = min(max_throughput, gate_state.queue_length)

            # Apply density-based reduction if connected zones are crowded
            connected_zones = [venue.get_zone(z) for z in gate.connected_zones]
            reduction = self._calculate_flow_reduction(state, connected_zones)
            actual_throughput = int(actual_throughput * reduction)

            # Update state
            gate_state.queue_length -= actual_throughput
            gate_state.throughput_rate = actual_throughput * 60 / dt_seconds
            gate_state.wait_time_minutes = (
                gate_state.queue_length / gate.capacity_per_minute
                if gate.capacity_per_minute > 0 else 0
            )
            gate_state.is_congested = gate_state.wait_time_minutes > 10

            # Add to connected zones
            if connected_zones and actual_throughput > 0:
                per_zone = actual_throughput // len(connected_zones)
                for zone in connected_zones:
                    if zone:
                        state.zone_states[zone.zone_id].current_occupancy += per_zone

            state.total_queuing -= actual_throughput
            total_entered += actual_throughput

        state.total_inside += total_entered
        state.overall_inflow_rate = total_entered * 60 / dt_seconds

    def _process_zone_flow(
        self,
        venue: Venue,
        state: CrowdState,
        dt_seconds: float
    ) -> None:
        """Process crowd flow between zones."""
        for zone in venue.zones:
            zone_state = state.zone_states[zone.zone_id]
            if zone_state.current_occupancy <= 0:
                continue

            # Calculate outflow based on density
            density = zone_state.density
            base_flow_rate = self.params.desired_speed * 60  # persons/min at free flow
            reduction = self._get_density_reduction(density)

            # Flow to connected zones
            connected = [venue.get_zone(z) for z in zone.connected_zones if venue.get_zone(z)]
            if not connected:
                continue

            # Calculate flow to each connected zone based on available capacity
            for target_zone in connected:
                target_state = state.zone_states[target_zone.zone_id]
                available_capacity = target_zone.capacity - target_state.current_occupancy

                if available_capacity <= 0:
                    continue

                flow = int(
                    min(
                        base_flow_rate * reduction * dt_seconds / 60 / len(connected),
                        zone_state.current_occupancy * 0.1,  # Max 10% move per step
                        available_capacity
                    )
                )

                if flow > 0:
                    zone_state.current_occupancy -= flow
                    target_state.current_occupancy += flow

    def _calculate_flow_reduction(
        self,
        state: CrowdState,
        zones: list[Zone | None]
    ) -> float:
        """Calculate flow reduction based on zone densities."""
        if not zones:
            return 1.0

        max_density = max(
            state.zone_states[z.zone_id].density
            for z in zones if z
        )
        return self._get_density_reduction(max_density)

    def _get_density_reduction(self, density: float) -> float:
        """Get flow reduction factor based on density."""
        if density < self.params.density_comfortable:
            return 1.0
        if density < self.params.density_crowded:
            return self.params.flow_reduction_crowded
        if density < self.params.density_dangerous:
            return self.params.flow_reduction_dangerous
        return self.params.flow_reduction_critical

    def _update_densities(self, venue: Venue, state: CrowdState) -> None:
        """Update density and risk levels for all zones."""
        for zone in venue.zones:
            zone_state = state.zone_states[zone.zone_id]
            zone_state.density = zone_state.current_occupancy / zone.area_sqm
            zone_state.risk_level = self._get_risk_level(zone_state.density)

    def _get_risk_level(self, density: float) -> str:
        """Determine risk level based on density."""
        if density < self.params.density_comfortable:
            return "safe"
        if density < self.params.density_crowded:
            return "moderate"
        if density < self.params.density_dangerous:
            return "high"
        return "critical"


def generate_arrival_curve(
    total_attendees: int,
    gates_open: datetime,
    event_start: datetime,
    pattern: str = "normal"
) -> list[tuple[float, float]]:
    """
    Generate arrival rate curve (minute, rate) for simulation.

    Patterns:
    - normal: Bell curve peaking 1hr before event
    - early_rush: Heavy early arrivals (K-pop concerts)
    - late_surge: Most arrive near start (football)
    - wave: Multiple peaks (festivals)
    """
    duration_minutes = (event_start - gates_open).total_seconds() / 60
    minutes = np.arange(0, duration_minutes + 1)

    if pattern == "normal":
        peak = duration_minutes * 0.5
        std = duration_minutes * 0.25
        curve = truncnorm.pdf(minutes, -peak/std, (duration_minutes-peak)/std, peak, std)
    elif pattern == "early_rush":
        peak = duration_minutes * 0.3
        std = duration_minutes * 0.15
        curve = truncnorm.pdf(minutes, -peak/std, (duration_minutes-peak)/std, peak, std)
    elif pattern == "late_surge":
        peak = duration_minutes * 0.8
        std = duration_minutes * 0.1
        curve = truncnorm.pdf(minutes, -peak/std, (duration_minutes-peak)/std, peak, std)
    else:  # wave
        # Multiple peaks for festival pattern
        curve = (
            0.3 * truncnorm.pdf(minutes, -30/20, 30/20, duration_minutes*0.3, 20) +
            0.4 * truncnorm.pdf(minutes, -30/20, 30/20, duration_minutes*0.5, 20) +
            0.3 * truncnorm.pdf(minutes, -30/20, 30/20, duration_minutes*0.7, 20)
        )

    # Normalize to total attendees
    curve = curve / curve.sum() * total_attendees

    return [(float(m), float(r)) for m, r in zip(minutes, curve)]
