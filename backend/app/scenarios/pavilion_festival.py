"""
Scenario: Chinese New Year Festival at Pavilion KL

Simulates wave pattern crowd throughout CNY celebration day.
Key challenges: Centre court congestion, food court overflow, parking full.
"""

PAVILION_FESTIVAL_SCENARIO = {
    "scenario_id": "pavilion-festival",
    "name": "Chinese New Year Festival - Pavilion KL",
    "description": "CNY celebration with 50,000 visitors throughout the day",
    "venue_id": "pavilion-kl",
    "event": {
        "event_id": "cny-pavilion-2024",
        "name": "Chinese New Year Celebration 2024",
        "event_type": "festival",
        "expected_attendance": 50000,  # Total over the day
        "peak_attendance": 22000,  # At any one time
        "start_time": "2024-02-10T10:00:00+08:00",
        "end_time": "2024-02-10T22:00:00+08:00",
        "gates_open": "2024-02-10T10:00:00+08:00"
    },
    "simulation_config": {
        "mode": "festival",  # Wave pattern, entry + exit
        "duration_minutes": 720,  # 12 hours
        "arrival_pattern": "wave",
        "turnover_rate": 0.3  # 30% leave per hour during steady state
    },
    "scenario_events": [
        {
            "time_minutes": 0,
            "event_type": "mall_opens",
            "description": "Mall opens - early shoppers arrive",
            "arrival_rate": 500  # per 30 min
        },
        {
            "time_minutes": 120,
            "event_type": "lunch_rush",
            "zone_id": "food-republic",
            "description": "Lunch rush - Food Republic packed",
            "density_spike": 3.5,
            "trigger_alerts": True
        },
        {
            "time_minutes": 240,
            "event_type": "lion_dance_start",
            "zone_id": "centre-court",
            "description": "Lion dance performance attracts 5000+ to Centre Court",
            "crowd_attraction": {
                "from_zones": ["level-1", "level-2", "level-3"],
                "to_zone": "centre-court",
                "flow_rate": 200  # per minute
            },
            "trigger_alerts": True
        },
        {
            "time_minutes": 270,
            "event_type": "centre_court_critical",
            "zone_id": "centre-court",
            "description": "Centre Court at 130% safe capacity",
            "density": 4.5,
            "trigger_alerts": True
        },
        {
            "time_minutes": 300,
            "event_type": "lion_dance_ends",
            "description": "Performance ends - crowd disperses",
            "dispersion_rate": 150  # per minute
        },
        {
            "time_minutes": 360,
            "event_type": "parking_full",
            "zone_id": "parking",
            "description": "All parking lots full",
            "trigger_alerts": True,
            "recommended_action": "Redirect to Fahrenheit 88 parking"
        },
        {
            "time_minutes": 420,
            "event_type": "dinner_rush",
            "zone_id": "food-republic",
            "description": "Dinner rush begins",
            "density_spike": 4.0
        },
        {
            "time_minutes": 540,
            "event_type": "fireworks_announcement",
            "zone_id": "outdoor-plaza",
            "description": "Fireworks announcement - crowd rush to outdoor plaza",
            "crowd_surge": 3000,
            "trigger_alerts": True
        },
        {
            "time_minutes": 600,
            "event_type": "fireworks_end",
            "description": "Fireworks end - gradual exit begins"
        }
    ],
    "crowd_distribution_by_hour": {
        "10:00": {"total": 5000, "peak_zone": "level-1"},
        "11:00": {"total": 10000, "peak_zone": "level-2"},
        "12:00": {"total": 15000, "peak_zone": "food-republic"},
        "13:00": {"total": 18000, "peak_zone": "level-1"},
        "14:00": {"total": 22000, "peak_zone": "centre-court"},
        "15:00": {"total": 20000, "peak_zone": "level-2"},
        "16:00": {"total": 18000, "peak_zone": "level-3"},
        "17:00": {"total": 20000, "peak_zone": "food-republic"},
        "18:00": {"total": 22000, "peak_zone": "dining-loft"},
        "19:00": {"total": 21000, "peak_zone": "outdoor-plaza"},
        "20:00": {"total": 18000, "peak_zone": "outdoor-plaza"},
        "21:00": {"total": 12000, "peak_zone": "level-1"}
    },
    "expected_alerts": [
        {
            "time_minutes": 120,
            "level": "warning",
            "title": "Food Republic queue overflow",
            "message": "Queue extending to Level 2 corridor",
            "actions": ["Open overflow seating", "Announce Dining Loft alternative"]
        },
        {
            "time_minutes": 270,
            "level": "critical",
            "title": "Centre Court overcrowded",
            "message": "Density at 4.5/m² - stop inflow immediately",
            "actions": ["Close Level 1 access to Centre Court", "Deploy crowd control", "Redirect to Level 2 viewing"]
        },
        {
            "time_minutes": 360,
            "level": "info",
            "title": "Parking capacity reached",
            "message": "Direct incoming vehicles to Fahrenheit 88",
            "actions": ["Update parking signs", "Announce on social media"]
        },
        {
            "time_minutes": 540,
            "level": "warning",
            "title": "Outdoor Plaza surge",
            "message": "Rapid crowd increase for fireworks",
            "actions": ["Open all plaza access points", "Deploy additional security"]
        }
    ],
    "demo_highlights": [
        "See wave pattern of crowds throughout the day",
        "Watch Centre Court turn critical during lion dance",
        "Observe food court queue visualization",
        "See parking capacity alert and redirect recommendation"
    ]
}
