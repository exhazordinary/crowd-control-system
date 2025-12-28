"""
Venue and Event Data Loader.

Loads venue configurations from JSON files.
"""

import json
from pathlib import Path
from typing import Optional

from app.models.venue import Venue, Gate, Zone, VenueLocation, VenueType


# Path to data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"


class VenueLoader:
    """Load venue configurations."""

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self._venues_cache: dict[str, Venue] = {}

    def load_venue(self, venue_id: str) -> Optional[Venue]:
        """Load a venue by ID."""
        if venue_id in self._venues_cache:
            return self._venues_cache[venue_id]

        venue_file = self.data_dir / "venues" / f"{venue_id}.json"
        if not venue_file.exists():
            return None

        with open(venue_file) as f:
            data = json.load(f)

        venue = self._parse_venue(data)
        self._venues_cache[venue_id] = venue
        return venue

    def load_all_venues(self) -> list[Venue]:
        """Load all available venues."""
        venues_dir = self.data_dir / "venues"
        if not venues_dir.exists():
            return []

        venues = []
        for venue_file in venues_dir.glob("*.json"):
            with open(venue_file) as f:
                data = json.load(f)
            venues.append(self._parse_venue(data))

        return venues

    def _parse_venue(self, data: dict) -> Venue:
        """Parse venue data from dict."""
        gates = [
            Gate(
                gate_id=g["gate_id"],
                name=g["name"],
                capacity_per_minute=g.get("capacity_per_minute", 200),
                location=tuple(g.get("location", [0, 0])),
                is_emergency_exit=g.get("is_emergency_exit", False),
                connected_zones=g.get("connected_zones", [])
            )
            for g in data.get("gates", [])
        ]

        zones = [
            Zone(
                zone_id=z["zone_id"],
                name=z["name"],
                capacity=z["capacity"],
                area_sqm=z.get("area_sqm", z["capacity"] / 2),
                zone_type=z.get("zone_type", "general"),
                connected_zones=z.get("connected_zones", []),
                connected_gates=z.get("connected_gates", []),
                svg_path=z.get("svg_path")
            )
            for z in data.get("zones", [])
        ]

        location_data = data.get("location", {})
        location = VenueLocation(
            lat=location_data.get("lat", 3.0),
            lng=location_data.get("lng", 101.0),
            address=location_data.get("address", ""),
            city=location_data.get("city", "Kuala Lumpur")
        )

        return Venue(
            venue_id=data["venue_id"],
            name=data["name"],
            venue_type=VenueType(data.get("venue_type", "stadium")),
            total_capacity=data["total_capacity"],
            gates=gates,
            zones=zones,
            location=location,
            floor_plan_svg=data.get("floor_plan_svg")
        )


# Convenience functions
_loader = VenueLoader()


def load_venue(venue_id: str) -> Optional[Venue]:
    """Load a venue by ID."""
    return _loader.load_venue(venue_id)


def load_all_venues() -> list[Venue]:
    """Load all venues."""
    return _loader.load_all_venues()
