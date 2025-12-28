"""Event data models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class EventType(str, Enum):
    CONCERT = "concert"
    FOOTBALL = "football"
    FESTIVAL = "festival"
    CONFERENCE = "conference"
    RALLY = "rally"


class TicketCategory(BaseModel):
    """Ticket category configuration."""
    category_id: str
    name: str  # "VIP", "Standard", "Standing"
    zone_id: str
    price_myr: float
    quantity_sold: int
    assigned_gates: list[str] = Field(default_factory=list)


class TransportLink(BaseModel):
    """Public transport connection to venue."""
    transport_type: str  # "lrt", "mrt", "bus", "monorail"
    station_name: str
    walking_distance_meters: int
    peak_capacity_per_hour: int
    schedule_frequency_minutes: int = 10


class Event(BaseModel):
    """Event configuration."""
    event_id: str
    name: str
    venue_id: str
    event_type: EventType
    start_time: datetime
    end_time: datetime
    gates_open: Optional[datetime] = None
    expected_attendance: int
    ticket_categories: list[TicketCategory] = Field(default_factory=list)
    transport_links: list[TransportLink] = Field(default_factory=list)

    @property
    def duration_hours(self) -> float:
        """Event duration in hours."""
        return (self.end_time - self.start_time).total_seconds() / 3600

    @property
    def gates_open_time(self) -> datetime:
        """When gates open (defaults to 2 hours before start)."""
        if self.gates_open:
            return self.gates_open
        from datetime import timedelta
        return self.start_time - timedelta(hours=2)


class EventCreate(BaseModel):
    """Request body for creating an event."""
    name: str
    venue_id: str
    event_type: EventType
    start_time: datetime
    end_time: datetime
    gates_open: Optional[datetime] = None
    expected_attendance: int
    ticket_categories: list[TicketCategory] = Field(default_factory=list)


class EventResponse(BaseModel):
    """API response for event."""
    event_id: str
    name: str
    venue_id: str
    event_type: EventType
    start_time: datetime
    end_time: datetime
    expected_attendance: int


class EventDetailResponse(Event):
    """API response for event details."""
    venue_name: Optional[str] = None
