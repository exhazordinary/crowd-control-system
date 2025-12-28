"""
Scenario: K-Pop Concert Entry Rush at Axiata Arena

Simulates 15,500 BLACKPINK fans entering for concert with early queue behavior.
Key challenges: Moshpit density, merchandise rush, scanner delays.
"""

AXIATA_CONCERT_SCENARIO = {
    "scenario_id": "axiata-concert",
    "name": "K-Pop Concert Entry - BLACKPINK",
    "description": "15,500 fans entering Axiata Arena for BLACKPINK World Tour",
    "venue_id": "axiata-arena",
    "event": {
        "event_id": "blackpink-kl-2024",
        "name": "BLACKPINK World Tour - Kuala Lumpur",
        "event_type": "concert",
        "expected_attendance": 15500,
        "start_time": "2024-06-20T20:00:00+08:00",
        "end_time": "2024-06-20T23:00:00+08:00",
        "gates_open": "2024-06-20T17:00:00+08:00"
    },
    "simulation_config": {
        "mode": "entry",
        "duration_minutes": 180,  # 3 hours from gates open to show start
        "arrival_pattern": "early_rush",  # K-pop fans arrive very early
        "pre_queue": 2000  # Fans queuing before gates open
    },
    "scenario_events": [
        {
            "time_minutes": -60,
            "event_type": "early_queue",
            "description": "2000 fans already queuing since morning",
            "queue_distribution": {
                "main-entrance": 1200,
                "east-entrance": 500,
                "merch-gate": 300
            }
        },
        {
            "time_minutes": 0,
            "event_type": "gates_open",
            "description": "Gates open - rush begins",
            "trigger_alerts": False
        },
        {
            "time_minutes": 15,
            "event_type": "merch_rush",
            "zone_id": "merch-area",
            "description": "Merchandise area at 200% capacity",
            "density_spike": 5.0,
            "trigger_alerts": True
        },
        {
            "time_minutes": 30,
            "event_type": "moshpit_filling",
            "zone_id": "standing-a",
            "description": "Moshpit (Standing A) filling rapidly",
            "density_increase_rate": 0.5  # persons/m² per minute
        },
        {
            "time_minutes": 45,
            "event_type": "moshpit_warning",
            "zone_id": "standing-a",
            "description": "Moshpit approaching unsafe density",
            "trigger_alerts": True
        },
        {
            "time_minutes": 60,
            "event_type": "scanner_malfunction",
            "gate_id": "main-entrance",
            "description": "QR scanner malfunction at Main Entrance",
            "throughput_reduction": 0.5,
            "duration_minutes": 15
        },
        {
            "time_minutes": 90,
            "event_type": "steady_state",
            "description": "Entry flow stabilizes, most fans inside"
        }
    ],
    "ticket_distribution": {
        "standing-a": {"name": "CAT 1 - Moshpit", "quantity": 3000, "price_myr": 988},
        "standing-b": {"name": "CAT 2 - Standing", "quantity": 4000, "price_myr": 788},
        "seated-lower": {"name": "CAT 3 - Lower", "quantity": 4500, "price_myr": 588},
        "seated-upper": {"name": "CAT 4 - Upper", "quantity": 3500, "price_myr": 388},
        "vip-section": {"name": "VVIP", "quantity": 500, "price_myr": 1888}
    },
    "expected_alerts": [
        {
            "time_minutes": 15,
            "level": "critical",
            "title": "Merchandise area overcrowded",
            "message": "Density at 5.0/m² - stop entry immediately",
            "actions": ["Close merch-gate temporarily", "Redirect to main concourse"]
        },
        {
            "time_minutes": 45,
            "level": "warning",
            "title": "Moshpit density high",
            "message": "Standing Zone A at 4.2/m² - monitor closely",
            "actions": ["Slow CAT 1 entry", "Deploy safety personnel"]
        },
        {
            "time_minutes": 60,
            "level": "info",
            "title": "Scanner delay at Main Entrance",
            "message": "Throughput reduced - queue building",
            "actions": ["Open backup scanners", "Redirect to East Entrance"]
        }
    ],
    "demo_highlights": [
        "See early fan queue building before gates open",
        "Watch merchandise area turn red with overcrowding",
        "Observe moshpit density increasing in real-time",
        "See recommendation to delay VIP entry"
    ]
}
