"""
Enhanced AI Recommendation Engine.

Generates SPECIFIC, ACTIONABLE recommendations for event staff.
Includes exact times, gate names, and measurable impacts.

Key improvement: Non-technical staff can immediately act on recommendations.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from app.models.venue import Venue
from app.models.crowd import CrowdState
from app.models.alert import Recommendation


class RecommendationEngine:
    """
    Generates smart, actionable recommendations for crowd management.

    Recommendations are:
    - Specific: "Open Gate C at 18:30" not "Consider opening gates"
    - Actionable: Clear instructions for non-technical staff
    - Measurable: Includes expected impact in numbers
    - Prioritized: Critical actions first
    """

    def __init__(self):
        self._applied_recommendations: set[str] = set()
        self._recommendation_history: list[Recommendation] = []

    def generate(
        self,
        venue: Venue,
        state: CrowdState,
        current_time: Optional[datetime] = None,
        transport_arrivals: Optional[dict] = None,
        facility_states: Optional[list] = None
    ) -> list[Recommendation]:
        """
        Generate recommendations based on current state.

        Args:
            venue: Venue configuration
            state: Current crowd state
            current_time: Current simulation/event time
            transport_arrivals: Expected arrivals from transport simulator
            facility_states: Current facility queue states
        """
        current_time = current_time or datetime.now()
        recommendations: list[Recommendation] = []

        # Priority 1: Critical safety recommendations
        recommendations.extend(self._safety_recommendations(venue, state, current_time))

        # Priority 2: Gate management
        recommendations.extend(self._gate_recommendations(venue, state, current_time))

        # Priority 3: Transport-coordinated recommendations
        if transport_arrivals:
            recommendations.extend(
                self._transport_recommendations(venue, state, current_time, transport_arrivals)
            )

        # Priority 4: Routing and flow
        recommendations.extend(self._routing_recommendations(venue, state, current_time))

        # Priority 5: Timing adjustments
        recommendations.extend(self._timing_recommendations(venue, state, current_time))

        # Priority 6: Capacity management
        recommendations.extend(self._capacity_recommendations(venue, state, current_time))

        # Priority 7: Facility recommendations
        if facility_states:
            recommendations.extend(
                self._facility_recommendations(venue, state, current_time, facility_states)
            )

        # Sort by confidence and filter duplicates
        seen_titles = set()
        unique_recs = []
        for rec in sorted(recommendations, key=lambda r: r.confidence, reverse=True):
            if rec.title not in seen_titles:
                seen_titles.add(rec.title)
                unique_recs.append(rec)

        # Store history and return top recommendations
        self._recommendation_history.extend(unique_recs[:5])
        return unique_recs[:5]

    def _safety_recommendations(
        self,
        venue: Venue,
        state: CrowdState,
        current_time: datetime
    ) -> list[Recommendation]:
        """CRITICAL safety recommendations - highest priority."""
        recommendations = []

        # Check for crushing density (> 6 persons/m²)
        for zone in venue.zones:
            zone_state = state.zone_states.get(zone.zone_id)
            if not zone_state:
                continue

            if zone_state.density >= 6.0:
                recommendations.append(Recommendation(
                    recommendation_id=str(uuid4()),
                    event_id=state.event_id,
                    timestamp=current_time,
                    category="emergency",
                    title=f"EMERGENCY: Stop all entry to {zone.name}",
                    description=f"CRUSHING RISK - Density at {zone_state.density:.1f}/m² (safe: <4.0). "
                              f"Immediately halt entry and begin controlled exit.",
                    impact=f"Prevents injury to {zone_state.current_occupancy:,} people in zone",
                    affected_zones=[zone.zone_id],
                    confidence=1.0,
                    icon="alert-triangle"
                ))

            elif zone_state.density >= 4.5:
                # Find emergency exits for this zone
                emergency_exits = [
                    g for g in venue.gates
                    if g.is_emergency_exit and zone.zone_id in str(g.gate_id)
                ]
                exit_names = [e.name for e in emergency_exits] or ["nearest exits"]

                recommendations.append(Recommendation(
                    recommendation_id=str(uuid4()),
                    event_id=state.event_id,
                    timestamp=current_time,
                    category="safety",
                    title=f"Open emergency exits for {zone.name}",
                    description=f"Density at {zone_state.density:.1f}/m² approaching dangerous levels. "
                              f"Open {', '.join(exit_names)} to relieve pressure.",
                    impact=f"Reduces density for {zone_state.current_occupancy:,} people",
                    affected_zones=[zone.zone_id],
                    affected_gates=[e.gate_id for e in emergency_exits],
                    confidence=0.98,
                    icon="door-open"
                ))

        return recommendations

    def _gate_recommendations(
        self,
        venue: Venue,
        state: CrowdState,
        current_time: datetime
    ) -> list[Recommendation]:
        """Specific gate management recommendations with times."""
        recommendations = []

        # Analyze gate states
        congested_gates = []
        underutilized_gates = []
        closed_gates = []

        for gate in venue.gates:
            if gate.is_emergency_exit:
                continue

            gate_state = state.gate_states.get(gate.gate_id)
            if not gate_state:
                continue

            if gate_state.is_congested:
                congested_gates.append((gate, gate_state))
            elif gate.is_open and gate_state.queue_length < 100:
                underutilized_gates.append((gate, gate_state))

            if not gate.is_open:
                closed_gates.append(gate)

        # Recommend opening specific closed gates
        if congested_gates and closed_gates:
            for closed_gate in closed_gates[:2]:
                # Calculate impact
                total_congested_queue = sum(gs.queue_length for _, gs in congested_gates)
                expected_reduction = min(
                    closed_gate.capacity_per_minute * 10,  # 10 min of capacity
                    total_congested_queue // 3
                )

                recommendations.append(Recommendation(
                    recommendation_id=str(uuid4()),
                    event_id=state.event_id,
                    timestamp=current_time,
                    category="gate",
                    title=f"Open {closed_gate.name} now",
                    description=f"Queues at {', '.join(g.name for g, _ in congested_gates[:2])} exceed 2,000. "
                              f"Opening {closed_gate.name} adds {closed_gate.capacity_per_minute}/min capacity.",
                    impact=f"Reduces total queue by ~{expected_reduction:,} in 10 minutes",
                    affected_gates=[closed_gate.gate_id] + [g.gate_id for g, _ in congested_gates],
                    confidence=0.92,
                    icon="door-open"
                ))

        # Recommend redirecting crowds between gates
        if congested_gates and underutilized_gates:
            for congested, cong_state in congested_gates[:1]:
                for underutil, under_state in underutilized_gates[:1]:
                    queue_diff = cong_state.queue_length - under_state.queue_length
                    if queue_diff > 500:
                        recommendations.append(Recommendation(
                            recommendation_id=str(uuid4()),
                            event_id=state.event_id,
                            timestamp=current_time,
                            category="gate",
                            title=f"Redirect queue from {congested.name} to {underutil.name}",
                            description=f"{congested.name}: {cong_state.queue_length:,} queuing. "
                                      f"{underutil.name}: only {under_state.queue_length:,}. "
                                      f"Deploy staff to guide crowd.",
                            impact=f"Balances queues, saves ~{cong_state.wait_time_minutes - under_state.wait_time_minutes:.0f} min wait",
                            affected_gates=[congested.gate_id, underutil.gate_id],
                            confidence=0.85,
                            icon="arrow-right-left"
                        ))

        # Specific time-based gate opening
        for gate in venue.gates:
            gate_state = state.gate_states.get(gate.gate_id)
            if not gate_state or not gate.is_open:
                continue

            # If queue > 15 min wait, recommend immediate action
            if gate_state.wait_time_minutes > 15:
                action_time = current_time + timedelta(minutes=2)
                recommendations.append(Recommendation(
                    recommendation_id=str(uuid4()),
                    event_id=state.event_id,
                    timestamp=current_time,
                    category="gate",
                    title=f"Add scanning staff to {gate.name} by {action_time.strftime('%H:%M')}",
                    description=f"Wait time at {gate.name} is {gate_state.wait_time_minutes:.0f} min. "
                              f"Adding 2 more scanners increases throughput by 40%.",
                    impact=f"Reduces wait from {gate_state.wait_time_minutes:.0f} to ~{gate_state.wait_time_minutes * 0.6:.0f} min",
                    affected_gates=[gate.gate_id],
                    confidence=0.88,
                    icon="users"
                ))

        return recommendations

    def _transport_recommendations(
        self,
        venue: Venue,
        state: CrowdState,
        current_time: datetime,
        transport_arrivals: dict
    ) -> list[Recommendation]:
        """Transport-coordinated recommendations - KEY INNOVATION."""
        recommendations = []

        total_arriving = transport_arrivals.get("total_arrivals", 0)
        peak_time_str = transport_arrivals.get("peak_arrival_time")

        if total_arriving > 1500 and peak_time_str:
            try:
                peak_time = datetime.fromisoformat(peak_time_str)
                prep_time = peak_time - timedelta(minutes=5)

                recommendations.append(Recommendation(
                    recommendation_id=str(uuid4()),
                    event_id=state.event_id,
                    timestamp=current_time,
                    category="transport",
                    title=f"Prepare gates for LRT surge at {peak_time.strftime('%H:%M')}",
                    description=f"~{total_arriving:,} passengers arriving via LRT. "
                              f"Open Gate A and B by {prep_time.strftime('%H:%M')} to prevent bottleneck.",
                    impact=f"Prevents queue buildup of {total_arriving:,} at station entrance",
                    confidence=0.9,
                    icon="train"
                ))
            except (ValueError, TypeError):
                pass

        # Post-event transport coordination
        if "exit_recommendations" in transport_arrivals:
            for rec in transport_arrivals["exit_recommendations"][:2]:
                recommendations.append(Recommendation(
                    recommendation_id=str(uuid4()),
                    event_id=state.event_id,
                    timestamp=current_time,
                    category="transport",
                    title=rec.get("action", "Transport coordination"),
                    description=f"Coordinate exit with LRT departures to prevent platform overcrowding.",
                    impact=rec.get("impact", "Smooth exit flow"),
                    confidence=0.85,
                    icon="train"
                ))

        return recommendations

    def _routing_recommendations(
        self,
        venue: Venue,
        state: CrowdState,
        current_time: datetime
    ) -> list[Recommendation]:
        """Crowd routing recommendations."""
        recommendations = []

        # Find critical and safe zones
        critical_zones = []
        safe_zones = []

        for zone in venue.zones:
            zone_state = state.zone_states.get(zone.zone_id)
            if not zone_state:
                continue

            if zone_state.risk_level == "critical":
                critical_zones.append((zone, zone_state))
            elif zone_state.risk_level == "safe" and zone_state.current_occupancy < zone.capacity * 0.5:
                safe_zones.append((zone, zone_state))

        for critical, crit_state in critical_zones:
            # Find connected safe zones
            connected_safe = [
                (z, zs) for z, zs in safe_zones
                if z.zone_id in critical.connected_zones
            ]

            if connected_safe:
                target, target_state = connected_safe[0]
                overflow = crit_state.current_occupancy - int(critical.capacity * 0.7)

                recommendations.append(Recommendation(
                    recommendation_id=str(uuid4()),
                    event_id=state.event_id,
                    timestamp=current_time,
                    category="routing",
                    title=f"Redirect {overflow:,} people from {critical.name} to {target.name}",
                    description=f"{critical.name} at {crit_state.density:.1f}/m² density. "
                              f"{target.name} has {target.capacity - target_state.current_occupancy:,} capacity available.",
                    impact=f"Reduces {critical.name} density from {crit_state.density:.1f} to ~{crit_state.density * 0.7:.1f}/m²",
                    affected_zones=[critical.zone_id, target.zone_id],
                    confidence=0.82,
                    icon="route"
                ))

        return recommendations

    def _timing_recommendations(
        self,
        venue: Venue,
        state: CrowdState,
        current_time: datetime
    ) -> list[Recommendation]:
        """Event timing recommendations."""
        recommendations = []

        # Calculate total wait time situation
        total_queue = sum(gs.queue_length for gs in state.gate_states.values())
        total_gate_capacity = sum(
            g.capacity_per_minute for g in venue.gates
            if g.is_open and not g.is_emergency_exit
        )

        if total_gate_capacity > 0:
            avg_wait = total_queue / total_gate_capacity  # minutes
        else:
            avg_wait = 999

        if avg_wait > 20:
            delay_mins = int(avg_wait - 15)
            new_start = current_time + timedelta(minutes=delay_mins)

            recommendations.append(Recommendation(
                recommendation_id=str(uuid4()),
                event_id=state.event_id,
                timestamp=current_time,
                category="timing",
                title=f"Delay event start by {delay_mins} minutes to {new_start.strftime('%H:%M')}",
                description=f"Current queue: {total_queue:,} people with avg {avg_wait:.0f} min wait. "
                          f"Delaying ensures 95% of attendees are seated for start.",
                impact=f"Prevents {int(total_queue * 0.3):,} people from missing event start",
                confidence=0.75,
                icon="clock"
            ))

        # Staggered exit recommendation
        if state.total_inside > 20000:
            recommendations.append(Recommendation(
                recommendation_id=str(uuid4()),
                event_id=state.event_id,
                timestamp=current_time,
                category="timing",
                title="Announce staggered exit: North Stand first, others after 3 min",
                description=f"With {state.total_inside:,} attendees, staggered exit prevents dangerous "
                          f"crowding at exits and LRT station.",
                impact="Reduces peak exit density by 40%",
                confidence=0.8,
                icon="users"
            ))

        return recommendations

    def _capacity_recommendations(
        self,
        venue: Venue,
        state: CrowdState,
        current_time: datetime
    ) -> list[Recommendation]:
        """Capacity management recommendations."""
        recommendations = []

        for zone in venue.zones:
            zone_state = state.zone_states.get(zone.zone_id)
            if not zone_state:
                continue

            utilization = zone_state.current_occupancy / zone.capacity

            if utilization > 0.85:
                over_capacity = zone_state.current_occupancy - int(zone.capacity * 0.8)

                # Find entry gates to this zone
                entry_gates = [
                    g for g in venue.gates
                    if zone.zone_id in str(g.gate_id) or zone.zone_id in g.connected_zones
                ]
                gate_names = [g.name for g in entry_gates[:2]] or ["entry points"]

                recommendations.append(Recommendation(
                    recommendation_id=str(uuid4()),
                    event_id=state.event_id,
                    timestamp=current_time,
                    category="capacity",
                    title=f"Temporarily close entry to {zone.name}",
                    description=f"{zone.name} at {utilization*100:.0f}% capacity "
                              f"({zone_state.current_occupancy:,}/{zone.capacity:,}). "
                              f"Stop entry at {', '.join(gate_names)} until density drops.",
                    impact=f"Prevents {over_capacity:,} additional people entering overcrowded zone",
                    affected_zones=[zone.zone_id],
                    affected_gates=[g.gate_id for g in entry_gates],
                    confidence=0.9,
                    icon="hand"
                ))

        return recommendations

    def _facility_recommendations(
        self,
        venue: Venue,
        state: CrowdState,
        current_time: datetime,
        facility_states: list
    ) -> list[Recommendation]:
        """Facility and queue management recommendations."""
        recommendations = []

        for fstate in facility_states:
            if fstate.status == "overcrowded":
                recommendations.append(Recommendation(
                    recommendation_id=str(uuid4()),
                    event_id=state.event_id,
                    timestamp=current_time,
                    category="facilities",
                    title=f"Deploy additional staff to {fstate.facility_id.replace('-', ' ').title()}",
                    description=f"Wait time at {fstate.wait_time_minutes:.0f} minutes. "
                              f"Add 2 temporary service points or deploy portable facilities.",
                    impact=f"Reduces wait from {fstate.wait_time_minutes:.0f} to ~{fstate.wait_time_minutes * 0.5:.0f} min",
                    confidence=0.78,
                    icon="users"
                ))

        return recommendations

    def get_recommendation_summary(self) -> dict:
        """Get summary of all recommendations generated."""
        by_category = {}
        for rec in self._recommendation_history:
            cat = rec.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append({
                "title": rec.title,
                "timestamp": rec.timestamp.isoformat(),
                "confidence": rec.confidence
            })

        return {
            "total_recommendations": len(self._recommendation_history),
            "by_category": by_category,
            "high_confidence_count": sum(
                1 for r in self._recommendation_history if r.confidence >= 0.85
            )
        }
