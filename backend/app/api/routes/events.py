"""Event API routes."""

from fastapi import APIRouter, HTTPException
from uuid import uuid4

from app.models.event import Event, EventCreate, EventResponse, EventDetailResponse
from app.scenarios import SCENARIOS

router = APIRouter(prefix="/events", tags=["events"])

# In-memory event storage for demo
_events: dict[str, Event] = {}


def _init_demo_events():
    """Initialize demo events from scenarios."""
    for scenario_id, scenario in SCENARIOS.items():
        event_data = scenario["event"]
        event = Event(
            event_id=event_data["event_id"],
            name=event_data["name"],
            venue_id=scenario["venue_id"],
            event_type=event_data["event_type"],
            expected_attendance=event_data["expected_attendance"],
            start_time=event_data["start_time"],
            end_time=event_data["end_time"],
            gates_open=event_data.get("gates_open")
        )
        _events[event.event_id] = event


# Initialize on module load
_init_demo_events()


@router.get("", response_model=list[EventResponse])
async def list_events(venue_id: str | None = None):
    """List all events, optionally filtered by venue."""
    events = list(_events.values())
    if venue_id:
        events = [e for e in events if e.venue_id == venue_id]
    return [
        EventResponse(
            event_id=e.event_id,
            name=e.name,
            venue_id=e.venue_id,
            event_type=e.event_type,
            start_time=e.start_time,
            end_time=e.end_time,
            expected_attendance=e.expected_attendance
        )
        for e in events
    ]


@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event(event_id: str):
    """Get event details."""
    event = _events.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    return EventDetailResponse(**event.model_dump())


@router.post("", response_model=EventResponse)
async def create_event(event_create: EventCreate):
    """Create a new event."""
    event_id = f"event-{uuid4().hex[:8]}"
    event = Event(event_id=event_id, **event_create.model_dump())
    _events[event_id] = event
    return EventResponse(
        event_id=event.event_id,
        name=event.name,
        venue_id=event.venue_id,
        event_type=event.event_type,
        start_time=event.start_time,
        end_time=event.end_time,
        expected_attendance=event.expected_attendance
    )


@router.delete("/{event_id}")
async def delete_event(event_id: str):
    """Delete an event."""
    if event_id not in _events:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    del _events[event_id]
    return {"status": "deleted", "event_id": event_id}
