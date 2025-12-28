"""
Transport Timing Integration Module

Integrates LRT/Bus schedules with crowd flow predictions for Malaysian events.
Based on real data from Bukit Jalil LRT operations during major events.

References:
- LRT Bukit Jalil: 3-5 min frequency peak, 7-10 min off-peak
- Capacity: ~1,200 passengers per train
- Extended hours during events (up to 1am for concerts)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum
import numpy as np


class TransportType(str, Enum):
    LRT = "lrt"
    BUS = "bus"
    PRIVATE = "private"
    TAXI = "taxi"
    WALKING = "walking"


@dataclass
class TransportService:
    """Single transport service (e.g., one LRT train)"""
    transport_id: str
    transport_type: TransportType
    station: str
    scheduled_time: datetime
    capacity: int
    expected_passengers: int = 0
    walking_time_to_venue: int = 5  # minutes


@dataclass
class TransportSchedule:
    """Complete transport schedule for an event"""
    services: list[TransportService] = field(default_factory=list)

    # LRT Bukit Jalil defaults
    lrt_peak_frequency: int = 4  # minutes
    lrt_offpeak_frequency: int = 8  # minutes
    lrt_capacity: int = 1200
    lrt_walking_time: int = 5  # minutes to venue

    # Bus defaults
    bus_frequency: int = 15  # minutes
    bus_capacity: int = 50

    def add_lrt_schedule(
        self,
        start_time: datetime,
        end_time: datetime,
        peak_start: Optional[datetime] = None,
        peak_end: Optional[datetime] = None
    ):
        """Generate LRT arrivals for the event period"""
        current = start_time
        service_id = 0

        while current <= end_time:
            # Determine frequency based on peak hours
            if peak_start and peak_end and peak_start <= current <= peak_end:
                freq = self.lrt_peak_frequency
                load_factor = 0.95  # Near capacity during peak
            else:
                freq = self.lrt_offpeak_frequency
                load_factor = 0.7

            self.services.append(TransportService(
                transport_id=f"LRT-{service_id:04d}",
                transport_type=TransportType.LRT,
                station="Bukit Jalil",
                scheduled_time=current,
                capacity=self.lrt_capacity,
                expected_passengers=int(self.lrt_capacity * load_factor),
                walking_time_to_venue=self.lrt_walking_time
            ))

            current += timedelta(minutes=freq)
            service_id += 1


class TransportSimulator:
    """
    Simulates transport arrivals and their impact on crowd flow.

    Key innovation: Links LRT departure times to gate opening strategy
    to prevent overcrowding at transport hubs.
    """

    def __init__(self, schedule: TransportSchedule):
        self.schedule = schedule
        self.arrival_history: list[tuple[datetime, int]] = []

    def calculate_arrival_wave(
        self,
        current_time: datetime,
        window_minutes: int = 15
    ) -> dict:
        """
        Calculate expected arrivals in the next window based on transport schedule.

        Returns:
            dict with:
            - total_arrivals: int
            - arrivals_by_transport: dict
            - peak_arrival_time: datetime
            - recommended_gate_action: str
        """
        window_end = current_time + timedelta(minutes=window_minutes)

        arrivals_by_transport = {t: 0 for t in TransportType}
        arrival_times = []

        for service in self.schedule.services:
            # Account for walking time from station
            arrival_at_venue = service.scheduled_time + timedelta(
                minutes=service.walking_time_to_venue
            )

            if current_time <= arrival_at_venue <= window_end:
                arrivals_by_transport[service.transport_type] += service.expected_passengers
                arrival_times.append((arrival_at_venue, service.expected_passengers))

        total = sum(arrivals_by_transport.values())
        peak_time = None

        if arrival_times:
            # Find peak arrival minute
            arrival_times.sort(key=lambda x: x[0])
            peak_time = max(arrival_times, key=lambda x: x[1])[0]

        # Generate recommendation based on expected arrivals
        recommendation = self._generate_arrival_recommendation(
            total, arrivals_by_transport, peak_time, current_time
        )

        return {
            "total_arrivals": total,
            "arrivals_by_transport": {k.value: v for k, v in arrivals_by_transport.items()},
            "peak_arrival_time": peak_time.isoformat() if peak_time else None,
            "recommended_action": recommendation
        }

    def predict_exit_surge(
        self,
        event_end_time: datetime,
        total_attendees: int,
        exit_duration_minutes: int = 45
    ) -> list[dict]:
        """
        Predict crowd surge toward transport hubs after event.

        Key insight: Coordinate gate openings with LRT departures
        to prevent platform overcrowding.

        Returns list of recommendations with timing.
        """
        recommendations = []

        # Find LRT departures after event
        post_event_services = [
            s for s in self.schedule.services
            if s.transport_type == TransportType.LRT
            and event_end_time <= s.scheduled_time <= event_end_time + timedelta(minutes=exit_duration_minutes)
        ]

        if not post_event_services:
            return [{
                "time": event_end_time.isoformat(),
                "action": "No LRT services scheduled post-event. Recommend extending LRT hours.",
                "priority": "critical",
                "impact": "Prevents stranded attendees"
            }]

        # Calculate optimal exit timing
        lrt_capacity_total = sum(s.capacity for s in post_event_services)
        lrt_passengers_ratio = min(1.0, lrt_capacity_total / (total_attendees * 0.6))  # 60% use LRT

        # Generate staggered exit recommendations
        for i, service in enumerate(post_event_services[:5]):  # First 5 trains
            gate_open_time = service.scheduled_time - timedelta(
                minutes=self.schedule.lrt_walking_time + 3  # 3 min buffer
            )

            if i == 0:
                recommendations.append({
                    "time": gate_open_time.isoformat(),
                    "action": f"Open South Stand exits to catch {service.scheduled_time.strftime('%H:%M')} LRT",
                    "priority": "high",
                    "impact": f"Distributes {service.capacity} passengers to first train",
                    "gate_ids": ["gate-south-1", "gate-south-2"]
                })
            else:
                recommendations.append({
                    "time": gate_open_time.isoformat(),
                    "action": f"Release next section for {service.scheduled_time.strftime('%H:%M')} LRT departure",
                    "priority": "medium",
                    "impact": f"Manages flow of {service.capacity} passengers"
                })

        # Check capacity vs demand
        if lrt_passengers_ratio < 0.8:
            recommendations.insert(0, {
                "time": event_end_time.isoformat(),
                "action": "Request additional LRT services - capacity insufficient for crowd",
                "priority": "critical",
                "impact": f"Current capacity handles only {int(lrt_passengers_ratio*100)}% of expected LRT users"
            })

        return recommendations

    def _generate_arrival_recommendation(
        self,
        total: int,
        by_transport: dict,
        peak_time: Optional[datetime],
        current_time: datetime
    ) -> Optional[str]:
        """Generate actionable recommendation based on arrival patterns."""
        if total < 500:
            return None

        if total > 3000:
            return f"High arrival wave expected ({total:,} people). Open all gates immediately."

        if total > 1500:
            lrt_pct = by_transport.get(TransportType.LRT, 0) / total if total > 0 else 0
            if lrt_pct > 0.7 and peak_time:
                mins_until = (peak_time - current_time).total_seconds() / 60
                return f"LRT arrival surge in {int(mins_until)} minutes. Prepare Gate A and B for {int(total * lrt_pct):,} passengers."

        return None


@dataclass
class ParkingLot:
    """Parking facility with capacity tracking"""
    lot_id: str
    name: str
    capacity: int
    current_occupancy: int = 0
    entry_rate: int = 20  # vehicles per minute max
    exit_rate: int = 15  # vehicles per minute max
    distance_to_venue: int = 5  # walking minutes
    is_overflow: bool = False


class ParkingSimulator:
    """
    Simulates parking lot fill rates and overflow predictions.
    """

    def __init__(self, lots: list[ParkingLot]):
        self.lots = {lot.lot_id: lot for lot in lots}
        self.fill_history: list[tuple[datetime, dict]] = []

    def simulate_arrival(
        self,
        current_time: datetime,
        vehicles_arriving: int,
        minutes: int = 1
    ) -> list[dict]:
        """Simulate vehicle arrivals and return recommendations."""
        recommendations = []
        remaining = vehicles_arriving

        # Fill primary lots first, then overflow
        for lot in sorted(self.lots.values(), key=lambda x: (x.is_overflow, -x.capacity)):
            if remaining <= 0:
                break

            available = lot.capacity - lot.current_occupancy
            can_accept = min(remaining, available, lot.entry_rate * minutes)

            lot.current_occupancy += can_accept
            remaining -= can_accept

            # Check fill level
            fill_pct = lot.current_occupancy / lot.capacity

            if fill_pct >= 0.9 and not lot.is_overflow:
                recommendations.append({
                    "type": "parking",
                    "priority": "high",
                    "action": f"{lot.name} at {int(fill_pct*100)}% capacity. Direct traffic to overflow parking.",
                    "lot_id": lot.lot_id,
                    "fill_percentage": fill_pct
                })
            elif fill_pct >= 0.75:
                recommendations.append({
                    "type": "parking",
                    "priority": "medium",
                    "action": f"{lot.name} reaching capacity ({int(fill_pct*100)}%). Prepare overflow lot.",
                    "lot_id": lot.lot_id,
                    "fill_percentage": fill_pct
                })

        if remaining > 0:
            recommendations.append({
                "type": "parking",
                "priority": "critical",
                "action": f"All parking lots full! {remaining} vehicles cannot be accommodated.",
                "overflow_vehicles": remaining
            })

        # Record history
        self.fill_history.append((
            current_time,
            {lot.lot_id: lot.current_occupancy for lot in self.lots.values()}
        ))

        return recommendations

    def predict_overflow_time(
        self,
        arrival_rate: int,  # vehicles per minute
        current_time: datetime
    ) -> Optional[dict]:
        """Predict when parking will overflow."""
        total_available = sum(
            lot.capacity - lot.current_occupancy
            for lot in self.lots.values()
        )

        if arrival_rate <= 0:
            return None

        minutes_until_full = total_available / arrival_rate
        overflow_time = current_time + timedelta(minutes=minutes_until_full)

        return {
            "overflow_time": overflow_time.isoformat(),
            "minutes_until_full": int(minutes_until_full),
            "recommendation": f"Parking will overflow at {overflow_time.strftime('%H:%M')}. "
                            f"Activate overflow arrangements {int(minutes_until_full - 15)} minutes before."
        }


# Malaysian venue parking configurations
BUKIT_JALIL_PARKING = [
    ParkingLot("lot-a", "Parking Lot A (Main)", 3000),
    ParkingLot("lot-b", "Parking Lot B (East)", 2000),
    ParkingLot("lot-c", "Parking Lot C (West)", 1500),
    ParkingLot("lot-overflow", "Overflow Parking (Pavilion)", 1000, is_overflow=True),
]

AXIATA_PARKING = [
    ParkingLot("axiata-main", "Axiata Arena Parking", 1500),
    ParkingLot("axiata-overflow", "Stadium Parking Overflow", 800, is_overflow=True),
]
