"""
Data Import API Routes

Allows uploading of ticketing data, transport schedules, and event configurations
from CSV/JSON files. No hardware sensors required - uses existing datasets.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import csv
import json
import io

from app.services.data_store import (
    data_store,
    UploadedTicketingData,
    UploadedTransportData,
    UploadedScheduleData,
)


router = APIRouter(prefix="/data", tags=["Data Import"])


class TicketingData(BaseModel):
    """Parsed ticketing record"""
    ticket_id: str
    zone: str
    gate: str
    purchase_time: Optional[datetime]
    entry_time_estimate: Optional[str]
    seat_section: Optional[str] = None


class TransportData(BaseModel):
    """Parsed transport schedule"""
    transport_type: str  # lrt, bus, taxi
    station: str
    arrival_time: str
    capacity: int
    expected_passengers: int


class ImportResult(BaseModel):
    """Result of data import"""
    success: bool
    records_imported: int
    errors: list[str]
    summary: dict


# CSV Templates for download
TICKETING_TEMPLATE = """ticket_id,zone,gate,purchase_time,entry_time_estimate,seat_section
TK001,north-stand,gate-a,2024-01-15 10:30,19:00,A1
TK002,south-stand,gate-c,2024-01-15 14:22,19:15,B5
TK003,east-stand,gate-b,2024-01-15 09:00,18:45,C10
"""

TRANSPORT_TEMPLATE = """transport_type,station,arrival_time,capacity,expected_passengers
lrt,Bukit Jalil,18:30,1200,1100
lrt,Bukit Jalil,18:35,1200,1150
lrt,Bukit Jalil,18:40,1200,1200
bus,Stadium Bus Stop,18:35,50,45
bus,Stadium Bus Stop,18:50,50,48
"""

EVENT_SCHEDULE_TEMPLATE = """event_phase,start_time,end_time,description
gates_open,18:00,19:30,Entry period
event_start,19:30,19:30,Match kickoff
halftime,20:15,20:30,Half-time break
second_half,20:30,21:15,Second half
event_end,21:15,21:15,Final whistle
exit_period,21:15,22:30,Crowd exit
"""


@router.get("/templates/{template_type}")
async def get_template(template_type: str):
    """
    Download CSV template for data import.

    Available templates:
    - ticketing: Ticket sales data
    - transport: LRT/Bus schedules
    - schedule: Event schedule phases
    """
    templates = {
        "ticketing": TICKETING_TEMPLATE,
        "transport": TRANSPORT_TEMPLATE,
        "schedule": EVENT_SCHEDULE_TEMPLATE
    }

    if template_type not in templates:
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_type}' not found. Available: {list(templates.keys())}"
        )

    return JSONResponse({
        "template_type": template_type,
        "csv_content": templates[template_type],
        "instructions": f"Fill in the {template_type} data following the format above."
    })


@router.post("/upload/ticketing")
async def upload_ticketing_data(
    file: UploadFile = File(...),
    event_id: str = Query(default="custom-event", description="Event ID to associate data with")
) -> ImportResult:
    """
    Upload ticketing/attendance data from CSV.

    Expected columns:
    - ticket_id: Unique ticket identifier
    - zone: Zone name (e.g., north-stand, south-stand)
    - gate: Assigned entry gate
    - purchase_time: When ticket was purchased
    - entry_time_estimate: Expected arrival time
    - seat_section: (Optional) Seat section

    This data is used to predict crowd arrivals by zone and gate.
    """
    if not file.filename.endswith(('.csv', '.json')):
        raise HTTPException(400, "File must be CSV or JSON")

    content = await file.read()
    records = []
    errors = []

    try:
        if file.filename.endswith('.csv'):
            reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
            for i, row in enumerate(reader, start=2):
                try:
                    records.append(TicketingData(
                        ticket_id=row.get('ticket_id', f'TK{i:05d}'),
                        zone=row.get('zone', 'general'),
                        gate=row.get('gate', 'gate-a'),
                        purchase_time=datetime.fromisoformat(row['purchase_time']) if row.get('purchase_time') else None,
                        entry_time_estimate=row.get('entry_time_estimate'),
                        seat_section=row.get('seat_section')
                    ))
                except Exception as e:
                    errors.append(f"Row {i}: {str(e)}")
        else:
            data = json.loads(content)
            for i, item in enumerate(data, start=1):
                try:
                    records.append(TicketingData(**item))
                except Exception as e:
                    errors.append(f"Record {i}: {str(e)}")
    except Exception as e:
        raise HTTPException(400, f"Failed to parse file: {str(e)}")

    # Analyze the data
    zones = {}
    gates = {}
    entry_times = {}

    for record in records:
        zones[record.zone] = zones.get(record.zone, 0) + 1
        gates[record.gate] = gates.get(record.gate, 0) + 1
        if record.entry_time_estimate:
            hour = record.entry_time_estimate.split(':')[0] if ':' in record.entry_time_estimate else '19'
            entry_times[hour] = entry_times.get(hour, 0) + 1

    # Store in data store for simulation
    peak_hour = max(entry_times.items(), key=lambda x: x[1])[0] if entry_times else None

    uploaded_data = UploadedTicketingData(
        total_tickets=len(records),
        by_zone=zones,
        by_gate=gates,
        by_entry_hour=entry_times,
        peak_entry_hour=peak_hour,
        raw_records=[r.model_dump() for r in records[:1000]]  # Store up to 1000 records
    )
    data_store.store_ticketing(event_id, uploaded_data)

    # Check if a custom scenario was created
    custom_scenario = data_store.get_custom_scenario(event_id)

    return ImportResult(
        success=len(errors) == 0,
        records_imported=len(records),
        errors=errors[:10],  # First 10 errors
        summary={
            "total_tickets": len(records),
            "by_zone": zones,
            "by_gate": gates,
            "by_entry_hour": entry_times,
            "peak_entry_hour": peak_hour,
            "event_id": event_id,
            "scenario_created": custom_scenario is not None,
            "scenario_id": custom_scenario["scenario_id"] if custom_scenario else None,
        }
    )


@router.post("/upload/transport")
async def upload_transport_schedule(
    file: UploadFile = File(...),
    event_id: str = Query(default="custom-event", description="Event ID to associate data with")
) -> ImportResult:
    """
    Upload transport schedule (LRT/Bus arrivals).

    Expected columns:
    - transport_type: lrt, bus, taxi
    - station: Station/stop name
    - arrival_time: Scheduled arrival (HH:MM)
    - capacity: Vehicle capacity
    - expected_passengers: Expected passenger count

    This data is used to predict crowd arrival waves and
    coordinate gate openings with transport schedules.
    """
    if not file.filename.endswith(('.csv', '.json')):
        raise HTTPException(400, "File must be CSV or JSON")

    content = await file.read()
    records = []
    errors = []

    try:
        if file.filename.endswith('.csv'):
            reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
            for i, row in enumerate(reader, start=2):
                try:
                    records.append(TransportData(
                        transport_type=row.get('transport_type', 'lrt'),
                        station=row.get('station', 'Bukit Jalil'),
                        arrival_time=row.get('arrival_time', '18:00'),
                        capacity=int(row.get('capacity', 1200)),
                        expected_passengers=int(row.get('expected_passengers', 1000))
                    ))
                except Exception as e:
                    errors.append(f"Row {i}: {str(e)}")
        else:
            data = json.loads(content)
            for i, item in enumerate(data, start=1):
                try:
                    records.append(TransportData(**item))
                except Exception as e:
                    errors.append(f"Record {i}: {str(e)}")
    except Exception as e:
        raise HTTPException(400, f"Failed to parse file: {str(e)}")

    # Analyze transport data
    by_type = {}
    by_station = {}
    total_capacity = 0
    total_expected = 0

    for record in records:
        by_type[record.transport_type] = by_type.get(record.transport_type, 0) + 1
        by_station[record.station] = by_station.get(record.station, 0) + 1
        total_capacity += record.capacity
        total_expected += record.expected_passengers

    # Store in data store
    uploaded_data = UploadedTransportData(
        total_services=len(records),
        by_transport_type=by_type,
        by_station=by_station,
        total_capacity=total_capacity,
        total_expected_passengers=total_expected,
        arrivals=[r.model_dump() for r in records]
    )
    data_store.store_transport(event_id, uploaded_data)

    custom_scenario = data_store.get_custom_scenario(event_id)

    return ImportResult(
        success=len(errors) == 0,
        records_imported=len(records),
        errors=errors[:10],
        summary={
            "total_services": len(records),
            "by_transport_type": by_type,
            "by_station": by_station,
            "total_capacity": total_capacity,
            "total_expected_passengers": total_expected,
            "utilization_percent": round((total_expected / total_capacity) * 100, 1) if total_capacity > 0 else 0,
            "event_id": event_id,
            "scenario_updated": custom_scenario is not None,
        }
    )


@router.post("/upload/schedule")
async def upload_event_schedule(
    file: UploadFile = File(...),
    event_id: str = Query(default="custom-event", description="Event ID to associate data with")
) -> ImportResult:
    """
    Upload event schedule with phases.

    Expected columns:
    - event_phase: Phase name (gates_open, event_start, halftime, etc.)
    - start_time: Phase start (HH:MM)
    - end_time: Phase end (HH:MM)
    - description: Phase description

    Used to adjust simulation parameters during different event phases
    (e.g., higher restroom demand during halftime).
    """
    if not file.filename.endswith(('.csv', '.json')):
        raise HTTPException(400, "File must be CSV or JSON")

    content = await file.read()
    phases = []
    errors = []

    try:
        if file.filename.endswith('.csv'):
            reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
            for i, row in enumerate(reader, start=2):
                try:
                    phases.append({
                        "phase": row.get('event_phase'),
                        "start_time": row.get('start_time'),
                        "end_time": row.get('end_time'),
                        "description": row.get('description')
                    })
                except Exception as e:
                    errors.append(f"Row {i}: {str(e)}")
        else:
            phases = json.loads(content)
    except Exception as e:
        raise HTTPException(400, f"Failed to parse file: {str(e)}")

    # Calculate event duration and extract key times
    gates_open = None
    event_start = None
    event_end = None
    halftime_start = None
    halftime_end = None

    if phases:
        try:
            first_time = phases[0].get('start_time', '18:00')
            last_time = phases[-1].get('end_time', '22:00')

            start_h, start_m = map(int, first_time.split(':'))
            end_h, end_m = map(int, last_time.split(':'))

            duration_mins = (end_h * 60 + end_m) - (start_h * 60 + start_m)

            # Extract key times from phases
            for p in phases:
                phase_name = p.get('event_phase', p.get('phase', '')).lower()
                if 'gate' in phase_name and 'open' in phase_name:
                    gates_open = p.get('start_time')
                elif phase_name in ['event_start', 'start', 'kickoff']:
                    event_start = p.get('start_time')
                elif phase_name in ['event_end', 'end', 'finish']:
                    event_end = p.get('start_time') or p.get('end_time')
                elif 'half' in phase_name and 'time' in phase_name:
                    halftime_start = p.get('start_time')
                    halftime_end = p.get('end_time')
        except:
            duration_mins = 0
    else:
        duration_mins = 0

    # Store in data store
    uploaded_data = UploadedScheduleData(
        phases=phases,
        gates_open=gates_open,
        event_start=event_start,
        event_end=event_end,
        halftime_start=halftime_start,
        halftime_end=halftime_end,
    )
    data_store.store_schedule(event_id, uploaded_data)

    custom_scenario = data_store.get_custom_scenario(event_id)

    return ImportResult(
        success=len(errors) == 0,
        records_imported=len(phases),
        errors=errors[:10],
        summary={
            "total_phases": len(phases),
            "phases": [p.get('event_phase', p.get('phase')) for p in phases],
            "event_duration_minutes": duration_mins,
            "has_halftime": halftime_start is not None,
            "gates_open": gates_open,
            "event_start": event_start,
            "event_end": event_end,
            "event_id": event_id,
            "scenario_updated": custom_scenario is not None,
        }
    )


@router.get("/scenarios")
async def get_custom_scenarios():
    """Get all custom scenarios created from uploaded data."""
    return data_store.list_custom_scenarios()


@router.get("/scenarios/{event_id}")
async def get_custom_scenario(event_id: str):
    """Get a specific custom scenario."""
    scenario = data_store.get_custom_scenario(event_id)
    if not scenario:
        raise HTTPException(404, f"No custom scenario found for event: {event_id}")
    return scenario


@router.get("/sample/{data_type}")
async def get_sample_data(data_type: str, count: int = 100):
    """
    Generate sample data for testing.

    data_type options:
    - ticketing: Sample ticket sales
    - transport: Sample LRT/bus schedule
    - schedule: Sample event schedule
    """
    import random

    if data_type == "ticketing":
        zones = ["north-stand", "south-stand", "east-stand", "west-stand", "vip-section"]
        gates = ["gate-a", "gate-b", "gate-c", "gate-d"]

        samples = []
        for i in range(count):
            zone = random.choice(zones)
            gate = random.choice(gates)
            hour = random.randint(18, 19)
            minute = random.randint(0, 59)

            samples.append({
                "ticket_id": f"TK{i+1:05d}",
                "zone": zone,
                "gate": gate,
                "purchase_time": f"2024-01-{random.randint(1,15):02d} {random.randint(9,17):02d}:{random.randint(0,59):02d}",
                "entry_time_estimate": f"{hour}:{minute:02d}",
                "seat_section": f"{random.choice('ABCDEF')}{random.randint(1,50)}"
            })

        return {"data_type": "ticketing", "count": count, "data": samples}

    elif data_type == "transport":
        samples = []

        # LRT schedule (every 4-5 minutes during peak)
        for hour in [18, 19, 20, 21, 22]:
            for minute in range(0, 60, 4 if hour in [18, 19] else 8):
                load_factor = 0.95 if hour in [18, 19] else 0.7
                samples.append({
                    "transport_type": "lrt",
                    "station": "Bukit Jalil",
                    "arrival_time": f"{hour}:{minute:02d}",
                    "capacity": 1200,
                    "expected_passengers": int(1200 * load_factor * random.uniform(0.9, 1.1))
                })

        # Bus schedule
        for hour in [18, 19, 20, 21]:
            for minute in [0, 20, 40]:
                samples.append({
                    "transport_type": "bus",
                    "station": "Stadium Bus Stop",
                    "arrival_time": f"{hour}:{minute:02d}",
                    "capacity": 50,
                    "expected_passengers": random.randint(35, 50)
                })

        return {"data_type": "transport", "count": len(samples), "data": samples}

    elif data_type == "schedule":
        # Generate a realistic event schedule
        samples = [
            {"event_phase": "gates_open", "start_time": "17:00", "end_time": "19:30", "description": "Entry period - all gates open"},
            {"event_phase": "early_entry", "start_time": "17:00", "end_time": "18:00", "description": "VIP and early bird entry"},
            {"event_phase": "general_entry", "start_time": "18:00", "end_time": "19:30", "description": "General admission entry"},
            {"event_phase": "pre_show", "start_time": "19:00", "end_time": "19:30", "description": "Pre-show entertainment"},
            {"event_phase": "event_start", "start_time": "19:30", "end_time": "19:30", "description": "Main event begins"},
            {"event_phase": "first_half", "start_time": "19:30", "end_time": "20:15", "description": "First half / first set"},
            {"event_phase": "halftime", "start_time": "20:15", "end_time": "20:35", "description": "Half-time break - high restroom demand"},
            {"event_phase": "second_half", "start_time": "20:35", "end_time": "21:20", "description": "Second half / second set"},
            {"event_phase": "event_end", "start_time": "21:20", "end_time": "21:20", "description": "Main event ends"},
            {"event_phase": "exit_period", "start_time": "21:20", "end_time": "22:30", "description": "Crowd exit - staggered by zone"},
            {"event_phase": "late_exit", "start_time": "22:30", "end_time": "23:00", "description": "Stragglers and cleanup"},
        ]
        return {"data_type": "schedule", "count": len(samples), "data": samples}

    else:
        raise HTTPException(404, f"Unknown data type: {data_type}")
