"""
Risk Analysis Engine.

Detects bottlenecks, overcrowding, and safety hazards in real-time.
"""

from datetime import datetime
from uuid import uuid4

from app.models.venue import Venue
from app.models.crowd import CrowdState
from app.models.alert import Alert, AlertLevel, AlertCategory


class RiskAnalyzer:
    """Analyzes crowd state to detect risks and generate alerts."""

    # Density thresholds (persons/m^2)
    DENSITY_WARNING = 2.0
    DENSITY_CRITICAL = 4.0
    DENSITY_EMERGENCY = 6.0

    # Queue thresholds (persons)
    QUEUE_WARNING = 500
    QUEUE_CRITICAL = 1000
    QUEUE_EMERGENCY = 2000

    # Wait time thresholds (minutes)
    WAIT_WARNING = 15
    WAIT_CRITICAL = 30
    WAIT_EMERGENCY = 45

    def __init__(self):
        self._previous_alerts: set[str] = set()

    def analyze(self, venue: Venue, state: CrowdState) -> list[Alert]:
        """Analyze crowd state and return list of alerts."""
        alerts: list[Alert] = []

        alerts.extend(self._check_zone_densities(venue, state))
        alerts.extend(self._check_gate_queues(venue, state))
        alerts.extend(self._check_capacity_limits(venue, state))
        alerts.extend(self._check_flow_imbalances(venue, state))

        return alerts

    def _check_zone_densities(self, venue: Venue, state: CrowdState) -> list[Alert]:
        """Check zone densities for overcrowding."""
        alerts = []

        for zone in venue.zones:
            zone_state = state.zone_states.get(zone.zone_id)
            if not zone_state:
                continue

            density = zone_state.density
            alert_key = f"density_{zone.zone_id}"

            if density >= self.DENSITY_EMERGENCY:
                alerts.append(self._create_alert(
                    event_id=state.event_id,
                    level=AlertLevel.EMERGENCY,
                    category=AlertCategory.DENSITY,
                    zone_id=zone.zone_id,
                    title=f"EMERGENCY: {zone.name} critically overcrowded",
                    message=f"Density at {density:.1f}/m² - immediate evacuation required",
                    actions=[
                        f"Stop all entry to {zone.name} immediately",
                        "Open all emergency exits in this zone",
                        "Deploy crowd control personnel",
                        "Begin controlled evacuation"
                    ]
                ))
            elif density >= self.DENSITY_CRITICAL:
                alerts.append(self._create_alert(
                    event_id=state.event_id,
                    level=AlertLevel.CRITICAL,
                    category=AlertCategory.DENSITY,
                    zone_id=zone.zone_id,
                    title=f"Critical density in {zone.name}",
                    message=f"Density at {density:.1f}/m² - approaching unsafe levels",
                    actions=[
                        f"Temporarily close entry gates to {zone.name}",
                        "Redirect incoming crowd to adjacent zones",
                        "Prepare emergency exits for possible use"
                    ]
                ))
            elif density >= self.DENSITY_WARNING:
                alerts.append(self._create_alert(
                    event_id=state.event_id,
                    level=AlertLevel.WARNING,
                    category=AlertCategory.DENSITY,
                    zone_id=zone.zone_id,
                    title=f"High density in {zone.name}",
                    message=f"Density at {density:.1f}/m² - monitor closely",
                    actions=[
                        "Monitor zone closely",
                        "Consider slowing entry flow",
                        "Prepare alternative routing"
                    ]
                ))

        return alerts

    def _check_gate_queues(self, venue: Venue, state: CrowdState) -> list[Alert]:
        """Check gate queues for excessive wait times."""
        alerts = []

        for gate in venue.gates:
            gate_state = state.gate_states.get(gate.gate_id)
            if not gate_state:
                continue

            queue = gate_state.queue_length
            wait = gate_state.wait_time_minutes

            if queue >= self.QUEUE_EMERGENCY or wait >= self.WAIT_EMERGENCY:
                alerts.append(self._create_alert(
                    event_id=state.event_id,
                    level=AlertLevel.CRITICAL,
                    category=AlertCategory.QUEUE,
                    gate_id=gate.gate_id,
                    title=f"Severe congestion at {gate.name}",
                    message=f"Queue: {queue} people, Wait: {wait:.0f} min",
                    actions=[
                        "Open additional entry lanes",
                        "Deploy extra scanning staff",
                        "Redirect crowd to other gates",
                        "Consider fast-track entry (skip bag check)"
                    ]
                ))
            elif queue >= self.QUEUE_CRITICAL or wait >= self.WAIT_CRITICAL:
                alerts.append(self._create_alert(
                    event_id=state.event_id,
                    level=AlertLevel.WARNING,
                    category=AlertCategory.QUEUE,
                    gate_id=gate.gate_id,
                    title=f"Long queue at {gate.name}",
                    message=f"Queue: {queue} people, Wait: {wait:.0f} min",
                    actions=[
                        "Add additional scanning lanes",
                        "Announce alternative gates",
                        "Consider opening nearby gates early"
                    ]
                ))

        return alerts

    def _check_capacity_limits(self, venue: Venue, state: CrowdState) -> list[Alert]:
        """Check overall venue capacity."""
        alerts = []

        capacity_ratio = state.total_inside / venue.total_capacity if venue.total_capacity > 0 else 0

        if capacity_ratio >= 0.95:
            alerts.append(self._create_alert(
                event_id=state.event_id,
                level=AlertLevel.CRITICAL,
                category=AlertCategory.CAPACITY,
                title="Venue at maximum capacity",
                message=f"Venue is {capacity_ratio*100:.0f}% full ({state.total_inside:,} inside)",
                actions=[
                    "Stop all new entries immediately",
                    "Hold queues at all gates",
                    "Only allow entry as others exit"
                ]
            ))
        elif capacity_ratio >= 0.85:
            alerts.append(self._create_alert(
                event_id=state.event_id,
                level=AlertLevel.WARNING,
                category=AlertCategory.CAPACITY,
                title="Venue approaching capacity",
                message=f"Venue is {capacity_ratio*100:.0f}% full ({state.total_inside:,} inside)",
                actions=[
                    "Slow entry rate at all gates",
                    "Prepare for capacity limit enforcement"
                ]
            ))

        return alerts

    def _check_flow_imbalances(self, venue: Venue, state: CrowdState) -> list[Alert]:
        """Check for flow imbalances that could cause bottlenecks."""
        alerts = []

        # Check if one gate is handling disproportionate load
        gate_throughputs = [
            (g.gate_id, state.gate_states[g.gate_id].throughput_rate)
            for g in venue.gates
            if g.is_open and g.gate_id in state.gate_states
        ]

        if len(gate_throughputs) < 2:
            return alerts

        total_throughput = sum(t for _, t in gate_throughputs)
        if total_throughput == 0:
            return alerts

        for gate_id, throughput in gate_throughputs:
            ratio = throughput / total_throughput
            if ratio > 0.5 and len(gate_throughputs) >= 3:
                gate = venue.get_gate(gate_id)
                alerts.append(self._create_alert(
                    event_id=state.event_id,
                    level=AlertLevel.INFO,
                    category=AlertCategory.FLOW,
                    gate_id=gate_id,
                    title=f"Unbalanced flow at {gate.name if gate else gate_id}",
                    message=f"This gate handling {ratio*100:.0f}% of all entries",
                    actions=[
                        "Redirect crowd to less busy gates",
                        "Improve signage to other entrances"
                    ]
                ))

        return alerts

    def _create_alert(
        self,
        event_id: str,
        level: AlertLevel,
        category: AlertCategory,
        title: str,
        message: str,
        actions: list[str],
        zone_id: str | None = None,
        gate_id: str | None = None
    ) -> Alert:
        """Create a new alert."""
        return Alert(
            alert_id=str(uuid4()),
            event_id=event_id,
            timestamp=datetime.now(),
            level=level,
            category=category,
            zone_id=zone_id,
            gate_id=gate_id,
            title=title,
            message=message,
            suggested_actions=actions
        )
