"""
Facility Queue Simulation Module

Simulates restroom queues, food court congestion, and merchandise areas.
Uses empirical data for service times and arrival patterns during events.

Key insights:
- Half-time/intermission creates 10x normal restroom demand
- Female restrooms: 3 min avg service time
- Male restrooms: 2 min avg service time
- Food court peak: 15-20 min before event, half-time
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import numpy as np
from datetime import datetime, timedelta


class FacilityType(str, Enum):
    RESTROOM_MALE = "restroom_male"
    RESTROOM_FEMALE = "restroom_female"
    RESTROOM_ACCESSIBLE = "restroom_accessible"
    FOOD_COURT = "food_court"
    FOOD_STALL = "food_stall"
    MERCHANDISE = "merchandise"
    ATM = "atm"
    FIRST_AID = "first_aid"


@dataclass
class Facility:
    """Single facility with queue tracking"""
    facility_id: str
    facility_type: FacilityType
    name: str
    location: str  # Zone ID
    capacity: int  # Number of service points (stalls, counters)
    service_time_avg: float  # seconds per person
    service_time_std: float  # standard deviation
    current_queue: int = 0
    total_served: int = 0
    is_operational: bool = True


@dataclass
class FacilityState:
    """Current state of a facility"""
    facility_id: str
    current_queue: int
    wait_time_minutes: float
    utilization_percent: float
    status: str  # "normal", "busy", "overcrowded"


class FacilitySimulator:
    """
    Simulates queue dynamics for venue facilities.

    Uses M/M/c queueing model (Poisson arrivals, exponential service, c servers)
    with event-driven demand patterns.
    """

    # Service time constants (seconds)
    SERVICE_TIMES = {
        FacilityType.RESTROOM_MALE: (90, 30),  # 1.5 min avg, 0.5 std
        FacilityType.RESTROOM_FEMALE: (180, 45),  # 3 min avg, 0.75 std
        FacilityType.RESTROOM_ACCESSIBLE: (240, 60),  # 4 min avg
        FacilityType.FOOD_COURT: (180, 60),  # 3 min avg
        FacilityType.FOOD_STALL: (120, 30),  # 2 min avg
        FacilityType.MERCHANDISE: (300, 120),  # 5 min avg
        FacilityType.ATM: (90, 30),  # 1.5 min avg
        FacilityType.FIRST_AID: (600, 300),  # 10 min avg
    }

    # Demand multipliers during event phases
    DEMAND_MULTIPLIERS = {
        "pre_event": 0.5,
        "entry": 1.0,
        "event_start": 0.3,
        "halftime": 5.0,  # Huge spike
        "intermission": 4.0,
        "event_end": 0.5,
        "exit": 0.2,
    }

    def __init__(self, facilities: list[Facility]):
        self.facilities = {f.facility_id: f for f in facilities}
        self.history: list[tuple[datetime, dict]] = []

    def simulate_step(
        self,
        current_time: datetime,
        event_phase: str,
        zone_populations: dict[str, int],
        dt_seconds: int = 60
    ) -> list[FacilityState]:
        """
        Simulate one time step of facility queues.

        Args:
            current_time: Current simulation time
            event_phase: One of the DEMAND_MULTIPLIERS keys
            zone_populations: Current population by zone
            dt_seconds: Time step duration

        Returns:
            List of facility states with recommendations
        """
        states = []
        demand_mult = self.DEMAND_MULTIPLIERS.get(event_phase, 1.0)

        for fid, facility in self.facilities.items():
            if not facility.is_operational:
                continue

            # Calculate arrival rate based on zone population
            zone_pop = zone_populations.get(facility.location, 0)

            # Base arrival rate: ~2% of population uses restroom per 10 min
            if facility.facility_type in [FacilityType.RESTROOM_MALE, FacilityType.RESTROOM_FEMALE]:
                base_rate = zone_pop * 0.002 * (dt_seconds / 60)
            elif facility.facility_type == FacilityType.FOOD_COURT:
                base_rate = zone_pop * 0.005 * (dt_seconds / 60)
            elif facility.facility_type == FacilityType.MERCHANDISE:
                base_rate = zone_pop * 0.001 * (dt_seconds / 60)
            else:
                base_rate = zone_pop * 0.001 * (dt_seconds / 60)

            arrivals = int(base_rate * demand_mult * np.random.uniform(0.8, 1.2))

            # Calculate service completions
            service_rate = (facility.capacity * 60) / facility.service_time_avg  # per minute
            completions = int(min(
                facility.current_queue + arrivals,
                service_rate * (dt_seconds / 60)
            ))

            # Update queue
            facility.current_queue = max(0, facility.current_queue + arrivals - completions)
            facility.total_served += completions

            # Calculate wait time
            wait_time = (facility.current_queue * facility.service_time_avg) / (60 * facility.capacity)

            # Calculate utilization
            max_service = service_rate * (dt_seconds / 60)
            utilization = (completions / max_service * 100) if max_service > 0 else 0

            # Determine status
            if wait_time > 15:
                status = "overcrowded"
            elif wait_time > 7:
                status = "busy"
            else:
                status = "normal"

            states.append(FacilityState(
                facility_id=fid,
                current_queue=facility.current_queue,
                wait_time_minutes=round(wait_time, 1),
                utilization_percent=round(min(utilization, 100), 1),
                status=status
            ))

        # Record history
        self.history.append((
            current_time,
            {s.facility_id: s.current_queue for s in states}
        ))

        return states

    def get_recommendations(self, states: list[FacilityState]) -> list[dict]:
        """Generate recommendations based on facility states."""
        recs = []

        overcrowded = [s for s in states if s.status == "overcrowded"]
        busy = [s for s in states if s.status == "busy"]

        for state in overcrowded:
            facility = self.facilities[state.facility_id]
            recs.append({
                "priority": "high",
                "type": "facility_overcrowded",
                "facility_id": state.facility_id,
                "action": f"{facility.name} overcrowded ({state.wait_time_minutes:.0f} min wait). "
                         f"Consider deploying additional portable units or redirecting to alternate facilities.",
                "wait_time": state.wait_time_minutes
            })

        for state in busy:
            facility = self.facilities[state.facility_id]
            if state.wait_time_minutes > 10:
                recs.append({
                    "priority": "medium",
                    "type": "facility_busy",
                    "facility_id": state.facility_id,
                    "action": f"{facility.name} busy ({state.wait_time_minutes:.0f} min wait). "
                             f"Monitor for further congestion.",
                    "wait_time": state.wait_time_minutes
                })

        # Predict half-time surge
        restroom_states = [s for s in states if "restroom" in s.facility_id.lower()]
        if restroom_states:
            avg_wait = np.mean([s.wait_time_minutes for s in restroom_states])
            if avg_wait > 5:
                recs.append({
                    "priority": "medium",
                    "type": "halftime_warning",
                    "action": f"Current restroom wait averaging {avg_wait:.0f} min. "
                             f"Half-time will see 5x demand - prepare overflow facilities.",
                    "avg_wait": avg_wait
                })

        return recs

    def predict_halftime_impact(
        self,
        current_states: list[FacilityState],
        halftime_duration_minutes: int = 15,
        attendance: int = 50000
    ) -> dict:
        """
        Predict restroom demand during half-time.

        Empirical data: ~8-10% of attendees use restroom during half-time.
        """
        restroom_demand = int(attendance * 0.09)

        # Calculate total restroom capacity
        restroom_facilities = [
            f for f in self.facilities.values()
            if f.facility_type in [FacilityType.RESTROOM_MALE, FacilityType.RESTROOM_FEMALE]
        ]

        total_capacity_per_min = sum(
            (f.capacity * 60) / f.service_time_avg
            for f in restroom_facilities
        )

        capacity_in_halftime = total_capacity_per_min * halftime_duration_minutes
        shortfall = restroom_demand - capacity_in_halftime

        return {
            "expected_demand": restroom_demand,
            "capacity_in_halftime": int(capacity_in_halftime),
            "shortfall": int(max(0, shortfall)),
            "recommendation": (
                f"Half-time restroom demand: {restroom_demand:,} people. "
                f"Current capacity: {int(capacity_in_halftime):,} in {halftime_duration_minutes} min. "
                + (f"SHORTFALL of {int(shortfall):,} - deploy {int(shortfall/20)} additional portable units."
                   if shortfall > 0 else "Capacity sufficient.")
            ),
            "additional_units_needed": int(max(0, shortfall / 20))  # ~20 uses per portable per 15 min
        }


# Malaysian venue facility configurations
def create_bukit_jalil_facilities() -> list[Facility]:
    """Create facilities for Stadium Nasional Bukit Jalil"""
    facilities = []

    # Restrooms by zone
    zones = ["north-stand", "south-stand", "east-stand", "west-stand"]
    for zone in zones:
        facilities.extend([
            Facility(
                f"{zone}-restroom-m",
                FacilityType.RESTROOM_MALE,
                f"{zone.replace('-', ' ').title()} Male Restroom",
                zone,
                capacity=20,  # 20 urinals + stalls
                service_time_avg=90,
                service_time_std=30
            ),
            Facility(
                f"{zone}-restroom-f",
                FacilityType.RESTROOM_FEMALE,
                f"{zone.replace('-', ' ').title()} Female Restroom",
                zone,
                capacity=15,  # 15 stalls
                service_time_avg=180,
                service_time_std=45
            ),
        ])

    # Food courts
    facilities.extend([
        Facility(
            "food-court-main",
            FacilityType.FOOD_COURT,
            "Main Food Court",
            "concourse",
            capacity=50,
            service_time_avg=180,
            service_time_std=60
        ),
        Facility(
            "food-stalls-north",
            FacilityType.FOOD_STALL,
            "North Stand Food Stalls",
            "north-stand",
            capacity=10,
            service_time_avg=120,
            service_time_std=30
        ),
    ])

    # Merchandise
    facilities.append(Facility(
        "merch-main",
        FacilityType.MERCHANDISE,
        "Main Merchandise Store",
        "concourse",
        capacity=15,
        service_time_avg=300,
        service_time_std=120
    ))

    return facilities


def create_axiata_facilities() -> list[Facility]:
    """Create facilities for Axiata Arena"""
    return [
        Facility("axiata-restroom-m-1", FacilityType.RESTROOM_MALE, "Level 1 Male Restroom", "main-concourse", 12, 90, 30),
        Facility("axiata-restroom-f-1", FacilityType.RESTROOM_FEMALE, "Level 1 Female Restroom", "main-concourse", 10, 180, 45),
        Facility("axiata-restroom-m-2", FacilityType.RESTROOM_MALE, "Level 2 Male Restroom", "seated-upper", 8, 90, 30),
        Facility("axiata-restroom-f-2", FacilityType.RESTROOM_FEMALE, "Level 2 Female Restroom", "seated-upper", 8, 180, 45),
        Facility("axiata-food", FacilityType.FOOD_COURT, "Arena Food Court", "food-court", 30, 180, 60),
        Facility("axiata-merch", FacilityType.MERCHANDISE, "Merchandise Booth", "merch-area", 8, 300, 120),
    ]
