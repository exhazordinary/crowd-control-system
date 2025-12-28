"""
In-memory data store for uploaded event data.
Stores ticketing, transport, and schedule data for use in simulations.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class UploadedTicketingData(BaseModel):
    """Aggregated ticketing data"""
    total_tickets: int
    by_zone: dict[str, int]
    by_gate: dict[str, int]
    by_entry_hour: dict[str, int]
    peak_entry_hour: Optional[str] = None
    raw_records: list[dict] = []


class UploadedTransportData(BaseModel):
    """Aggregated transport schedule"""
    total_services: int
    by_transport_type: dict[str, int]
    by_station: dict[str, int]
    total_capacity: int
    total_expected_passengers: int
    arrivals: list[dict] = []  # Time-sorted transport arrivals


class UploadedScheduleData(BaseModel):
    """Event schedule phases"""
    phases: list[dict]
    gates_open: Optional[str] = None
    event_start: Optional[str] = None
    event_end: Optional[str] = None
    halftime_start: Optional[str] = None
    halftime_end: Optional[str] = None


class EventDataStore:
    """Stores uploaded data for creating custom scenarios"""

    def __init__(self):
        self._ticketing: dict[str, UploadedTicketingData] = {}
        self._transport: dict[str, UploadedTransportData] = {}
        self._schedule: dict[str, UploadedScheduleData] = {}
        self._custom_scenarios: dict[str, dict] = {}

    def store_ticketing(self, event_id: str, data: UploadedTicketingData):
        self._ticketing[event_id] = data
        self._try_create_scenario(event_id)

    def store_transport(self, event_id: str, data: UploadedTransportData):
        self._transport[event_id] = data
        self._try_create_scenario(event_id)

    def store_schedule(self, event_id: str, data: UploadedScheduleData):
        self._schedule[event_id] = data
        self._try_create_scenario(event_id)

    def get_ticketing(self, event_id: str) -> Optional[UploadedTicketingData]:
        return self._ticketing.get(event_id)

    def get_transport(self, event_id: str) -> Optional[UploadedTransportData]:
        return self._transport.get(event_id)

    def get_schedule(self, event_id: str) -> Optional[UploadedScheduleData]:
        return self._schedule.get(event_id)

    def _try_create_scenario(self, event_id: str):
        """Auto-create scenario when we have enough data"""
        ticketing = self._ticketing.get(event_id)
        if not ticketing:
            return

        schedule = self._schedule.get(event_id)
        transport = self._transport.get(event_id)

        # Determine event times
        gates_open = "18:00"
        event_start = "19:30"
        event_end = "22:00"

        if schedule:
            gates_open = schedule.gates_open or gates_open
            event_start = schedule.event_start or event_start
            event_end = schedule.event_end or event_end

        # Create custom scenario
        today = datetime.now().strftime("%Y-%m-%d")

        self._custom_scenarios[event_id] = {
            "scenario_id": f"custom-{event_id}",
            "name": f"Custom Event: {event_id}",
            "description": f"Custom scenario from uploaded data ({ticketing.total_tickets} tickets)",
            "venue_id": "bukit-jalil",  # Default venue
            "event_type": "custom",
            "event": {
                "name": f"Custom Event {event_id}",
                "start_time": f"{today}T{event_start}:00",
                "gates_open": f"{today}T{gates_open}:00",
                "end_time": f"{today}T{event_end}:00",
                "expected_attendance": ticketing.total_tickets,
            },
            "simulation_config": {
                "arrival_pattern": "normal",
                "zone_distribution": ticketing.by_zone,
                "gate_distribution": ticketing.by_gate,
                "transport_enabled": transport is not None,
            },
            "uploaded_data": {
                "ticketing": ticketing.model_dump() if ticketing else None,
                "transport": transport.model_dump() if transport else None,
                "schedule": schedule.model_dump() if schedule else None,
            }
        }

    def get_custom_scenario(self, event_id: str) -> Optional[dict]:
        return self._custom_scenarios.get(event_id)

    def list_custom_scenarios(self) -> list[dict]:
        return list(self._custom_scenarios.values())

    def get_all_event_ids(self) -> list[str]:
        """Get all event IDs that have any uploaded data"""
        all_ids = set(self._ticketing.keys()) | set(self._transport.keys()) | set(self._schedule.keys())
        return list(all_ids)


# Global singleton
data_store = EventDataStore()
