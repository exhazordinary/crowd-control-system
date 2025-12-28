"""
Scenario: Stadium Exit Rush at Bukit Jalil

Simulates 75,000 fans exiting after a JDT vs Selangor football match.
Key challenges: Gate congestion, LRT overcrowding, parking traffic.
"""

from datetime import datetime

BUKIT_JALIL_EXIT_SCENARIO = {
    "scenario_id": "bukit-jalil-exit",
    "name": "Stadium Exit Rush - JDT vs Selangor",
    "description": "75,000 fans exiting Bukit Jalil after Malaysia Super League match",
    "venue_id": "bukit-jalil",
    "event": {
        "event_id": "jdt-selangor-2024",
        "name": "Malaysia Super League: JDT vs Selangor FC",
        "event_type": "football",
        "expected_attendance": 75000,
        "start_time": "2024-03-15T20:00:00+08:00",
        "end_time": "2024-03-15T22:00:00+08:00",
        "gates_open": "2024-03-15T17:30:00+08:00"
    },
    "simulation_config": {
        "mode": "exit",  # Focus on exit flow
        "duration_minutes": 60,  # 1 hour post-match
        "arrival_pattern": "late_surge",  # Most exit immediately
        "initial_occupancy": {
            "north-stand": 20000,
            "south-stand": 23000,
            "east-stand": 18000,
            "west-stand": 12000,
            "vip-section": 2000
        }
    },
    "scenario_events": [
        {
            "time_minutes": 0,
            "event_type": "match_ends",
            "description": "Final whistle - mass exit begins",
            "trigger_alerts": True
        },
        {
            "time_minutes": 5,
            "event_type": "celebration_delay",
            "zone_id": "south-stand",
            "description": "JDT fans celebrating, delaying exit from South Stand",
            "flow_modifier": 0.3
        },
        {
            "time_minutes": 10,
            "event_type": "gate_congestion",
            "gate_id": "gate-south",
            "description": "Gate B reaches critical queue length",
            "queue_surge": 4500
        },
        {
            "time_minutes": 15,
            "event_type": "parking_overflow",
            "zone_id": "parking-a",
            "description": "Parking Lot A gridlocked - traffic jam",
            "capacity_reduction": 0.5
        },
        {
            "time_minutes": 20,
            "event_type": "lrt_overcrowding",
            "zone_id": "lrt-station",
            "description": "LRT Bukit Jalil at 150% capacity",
            "trigger_alerts": True
        },
        {
            "time_minutes": 30,
            "event_type": "flow_normalization",
            "description": "Exit flow begins to normalize",
            "flow_modifier": 1.0
        }
    ],
    "expected_alerts": [
        {
            "time_minutes": 10,
            "level": "critical",
            "title": "Gate B queue exceeds 4000",
            "message": "South Gate queue critical - immediate action required",
            "actions": ["Open auxiliary exits", "Redirect to Gate C and D"]
        },
        {
            "time_minutes": 20,
            "level": "warning",
            "title": "LRT station overcrowded",
            "message": "Platform density unsafe - request additional trains",
            "actions": ["Deploy crowd control", "Announce bus alternatives"]
        },
        {
            "time_minutes": 15,
            "level": "info",
            "title": "Staged exit recommended",
            "message": "Suggest releasing South Stand last to manage flow",
            "actions": ["Delay South Stand exit by 10 minutes"]
        }
    ],
    "demo_highlights": [
        "Watch density heatmap turn red at South Gate",
        "See recommendation to open emergency exits",
        "Observe LRT station overcrowding alert",
        "Notice flow rebalancing when gates adjusted"
    ]
}
