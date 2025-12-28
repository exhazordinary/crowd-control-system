"""Venue data models for Malaysian event locations."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class VenueType(str, Enum):
    STADIUM = "stadium"
    ARENA = "arena"
    CONVENTION = "convention"
    OUTDOOR = "outdoor"


class Gate(BaseModel):
    """Entry/exit gate configuration."""
    gate_id: str
    name: str
    capacity_per_minute: int = Field(ge=1, description="Max throughput per minute")
    location: tuple[float, float] = Field(description="(x, y) position on venue map")
    is_emergency_exit: bool = False
    connected_zones: list[str] = Field(default_factory=list)
    is_open: bool = True
    current_queue: int = 0


class Zone(BaseModel):
    """Venue zone/section configuration."""
    zone_id: str
    name: str
    capacity: int = Field(ge=1, description="Maximum safe capacity")
    area_sqm: float = Field(ge=1, description="Zone area in square meters")
    zone_type: str = Field(description="entry, seating, concourse, parking, exit, food")
    connected_zones: list[str] = Field(default_factory=list)
    connected_gates: list[str] = Field(default_factory=list)
    current_occupancy: int = 0
    svg_path: Optional[str] = None  # SVG path for visualization


class VenueLocation(BaseModel):
    """Geographic location of venue."""
    lat: float
    lng: float
    address: str
    city: str = "Kuala Lumpur"


class Venue(BaseModel):
    """Complete venue configuration."""
    venue_id: str
    name: str
    venue_type: VenueType
    total_capacity: int
    gates: list[Gate]
    zones: list[Zone]
    location: VenueLocation
    floor_plan_svg: Optional[str] = None

    def get_gate(self, gate_id: str) -> Optional[Gate]:
        """Get gate by ID."""
        return next((g for g in self.gates if g.gate_id == gate_id), None)

    def get_zone(self, zone_id: str) -> Optional[Zone]:
        """Get zone by ID."""
        return next((z for z in self.zones if z.zone_id == zone_id), None)

    def get_total_gate_capacity(self) -> int:
        """Total throughput capacity of all open gates."""
        return sum(g.capacity_per_minute for g in self.gates if g.is_open)


class VenueResponse(BaseModel):
    """API response for venue listing."""
    venue_id: str
    name: str
    venue_type: VenueType
    total_capacity: int
    location: VenueLocation


class VenueDetailResponse(Venue):
    """API response for venue details."""
    pass
