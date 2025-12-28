"""
Synthetic Data Generator for Malaysian Events.

Generates realistic crowd data including arrival patterns, ticket sales, and demographics.
"""

import random
from datetime import datetime, timedelta
from uuid import uuid4

import numpy as np
from scipy.stats import truncnorm

from app.models.event import Event, EventType, TicketCategory
from app.models.crowd import Agent, AgentState


class SyntheticDataGenerator:
    """Generate realistic Malaysian event crowd data."""

    # Malaysian demographic name pools
    MALAY_NAMES = ["Ahmad", "Muhammad", "Siti", "Nurul", "Mohd", "Nur", "Amir", "Aisyah", "Farid", "Fatimah"]
    CHINESE_NAMES = ["Tan", "Lee", "Wong", "Lim", "Ng", "Chan", "Ooi", "Koh", "Yeoh", "Teh"]
    INDIAN_NAMES = ["Kumar", "Raj", "Priya", "Anand", "Muthu", "Lakshmi", "Rajan", "Devi", "Suresh", "Kavitha"]

    def __init__(self, seed: int = 42):
        self._rng = np.random.default_rng(seed)
        random.seed(seed)

    def generate_arrival_times(
        self,
        total_attendees: int,
        gates_open: datetime,
        event_start: datetime,
        pattern: str = "normal"
    ) -> list[datetime]:
        """Generate arrival times based on pattern type."""
        duration_minutes = (event_start - gates_open).total_seconds() / 60

        patterns = {
            "normal": (0.5, 0.25),      # Peak at 50%, std 25%
            "early_rush": (0.3, 0.15),   # Peak at 30%, narrow std
            "late_surge": (0.8, 0.1),    # Peak at 80%, very narrow
        }

        if pattern in patterns:
            peak_ratio, std_ratio = patterns[pattern]
            peak = duration_minutes * peak_ratio
            std = duration_minutes * std_ratio

            arrival_minutes = truncnorm(
                (0 - peak) / std,
                (duration_minutes - peak) / std,
                loc=peak,
                scale=std
            ).rvs(total_attendees, random_state=self._rng)
        else:
            # Wave pattern for festivals
            arrival_minutes = self._generate_wave_arrivals(total_attendees, duration_minutes)

        return [
            gates_open + timedelta(minutes=float(m))
            for m in sorted(arrival_minutes)
        ]

    def _generate_wave_arrivals(self, total: int, duration: float) -> np.ndarray:
        """Generate wave pattern arrivals for festivals."""
        # Three peaks throughout the day
        peak1 = self._rng.normal(duration * 0.25, duration * 0.1, total // 3)
        peak2 = self._rng.normal(duration * 0.5, duration * 0.1, total // 3)
        peak3 = self._rng.normal(duration * 0.75, duration * 0.1, total - 2 * (total // 3))

        arrivals = np.concatenate([peak1, peak2, peak3])
        return np.clip(arrivals, 0, duration)

    def generate_ticket_distribution(
        self,
        venue_zones: list[dict],
        total_tickets: int,
        event_type: EventType
    ) -> list[TicketCategory]:
        """Generate realistic ticket sales distribution."""
        # Zone weight distributions by event type
        type_weights = {
            EventType.CONCERT: {
                "standing": 0.35, "seated-lower": 0.30, "seated-upper": 0.25, "vip": 0.10
            },
            EventType.FOOTBALL: {
                "north": 0.28, "south": 0.32, "east": 0.22, "west": 0.18
            },
            EventType.FESTIVAL: {
                "main": 0.25, "food": 0.20, "stage": 0.30, "outdoor": 0.25
            }
        }

        weights = type_weights.get(event_type, {})
        categories = []

        for zone in venue_zones:
            zone_id = zone.get("zone_id", zone.get("id", ""))
            zone_name = zone.get("name", zone_id)

            # Find matching weight or use default
            weight = 1.0 / len(venue_zones)
            for key, w in weights.items():
                if key in zone_id.lower() or key in zone_name.lower():
                    weight = w
                    break

            # Add some randomness
            weight *= self._rng.uniform(0.9, 1.1)
            quantity = int(total_tickets * weight)
            quantity = min(quantity, zone.get("capacity", quantity))

            # Determine price based on zone type
            base_price = 150.0  # MYR
            if "vip" in zone_name.lower():
                price = base_price * 4
            elif "standing" in zone_name.lower() or "moshpit" in zone_name.lower():
                price = base_price * 2.5
            elif "lower" in zone_name.lower():
                price = base_price * 1.5
            else:
                price = base_price

            categories.append(TicketCategory(
                category_id=f"cat-{zone_id}",
                name=zone_name,
                zone_id=zone_id,
                price_myr=price,
                quantity_sold=quantity,
                assigned_gates=zone.get("connected_gates", [])
            ))

        return categories

    def generate_agents(
        self,
        count: int,
        ticket_categories: list[TicketCategory],
        arrival_times: list[datetime]
    ) -> list[Agent]:
        """Generate individual agents for detailed simulation."""
        agents = []
        names = self._generate_malaysian_names(count)

        # Distribute agents across ticket categories
        category_counts = {}
        total_sold = sum(tc.quantity_sold for tc in ticket_categories)

        for tc in ticket_categories:
            ratio = tc.quantity_sold / total_sold if total_sold > 0 else 1 / len(ticket_categories)
            category_counts[tc.category_id] = int(count * ratio)

        agent_idx = 0
        for tc in ticket_categories:
            cat_count = category_counts.get(tc.category_id, 0)
            for _ in range(cat_count):
                if agent_idx >= count:
                    break

                agents.append(Agent(
                    agent_id=f"agent-{uuid4().hex[:8]}",
                    ticket_category=tc.category_id,
                    arrival_time=arrival_times[agent_idx] if agent_idx < len(arrival_times) else arrival_times[-1],
                    destination_zone=tc.zone_id,
                    target_gate=tc.assigned_gates[0] if tc.assigned_gates else None,
                    state=AgentState.APPROACHING
                ))
                agent_idx += 1

        return agents

    def _generate_malaysian_names(self, count: int) -> list[str]:
        """Generate realistic Malaysian names reflecting demographics."""
        # Approximate Malaysian demographics: 60% Malay, 25% Chinese, 10% Indian, 5% Others
        all_names = (
            self.MALAY_NAMES * 6 +
            self.CHINESE_NAMES * 3 +
            self.INDIAN_NAMES * 1
        )
        return [f"{random.choice(all_names)}_{i}" for i in range(count)]

    def generate_flow_timeseries(
        self,
        duration_minutes: int,
        zones: list[dict],
        pattern: str = "normal"
    ) -> list[dict]:
        """Generate time-series crowd flow data for visualization."""
        data = []

        for minute in range(duration_minutes):
            t = minute / duration_minutes  # Normalized time 0-1

            # Base flow pattern
            if pattern == "normal":
                flow_factor = np.exp(-((t - 0.5) ** 2) / 0.1)
            elif pattern == "early_rush":
                flow_factor = np.exp(-((t - 0.3) ** 2) / 0.05)
            elif pattern == "late_surge":
                flow_factor = np.exp(-((t - 0.8) ** 2) / 0.03)
            else:  # wave
                flow_factor = 0.3 * (
                    np.exp(-((t - 0.25) ** 2) / 0.02) +
                    np.exp(-((t - 0.5) ** 2) / 0.02) +
                    np.exp(-((t - 0.75) ** 2) / 0.02)
                )

            zone_densities = {}
            for zone in zones:
                zone_id = zone.get("zone_id", zone.get("id", ""))
                capacity = zone.get("capacity", 1000)
                area = zone.get("area_sqm", 500)

                # Simulate occupancy based on flow
                occupancy = int(capacity * flow_factor * self._rng.uniform(0.7, 1.0))
                density = occupancy / area if area > 0 else 0

                zone_densities[zone_id] = {
                    "occupancy": occupancy,
                    "density": round(density, 2),
                    "risk_level": self._get_risk_level(density)
                }

            data.append({
                "minute": minute,
                "flow_factor": round(flow_factor, 3),
                "zones": zone_densities
            })

        return data

    def _get_risk_level(self, density: float) -> str:
        """Determine risk level from density."""
        if density < 0.5:
            return "safe"
        if density < 2.0:
            return "moderate"
        if density < 4.0:
            return "high"
        return "critical"
