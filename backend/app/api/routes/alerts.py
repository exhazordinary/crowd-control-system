"""Alerts API routes."""

from fastapi import APIRouter, HTTPException

from app.models.alert import Alert, AlertLevel, AlertsOverview, Recommendation
from app.engine.risk_analyzer import RiskAnalyzer
from app.engine.recommender import RecommendationEngine
from app.data.loader import load_venue
from app.scenarios import SCENARIOS

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Store acknowledged alerts
_acknowledged_alerts: set[str] = set()


@router.get("/{event_id}", response_model=list[Alert])
async def get_alerts(event_id: str, level: AlertLevel | None = None):
    """Get active alerts for an event."""
    # Import here to avoid circular dependency
    from app.api.routes.simulation import _simulations

    if event_id not in _simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")

    sim_state = _simulations[event_id]
    scenario = SCENARIOS.get(sim_state.scenario)

    if not scenario:
        return []

    venue = load_venue(scenario["venue_id"])
    if not venue:
        return []

    risk_analyzer = RiskAnalyzer()
    alerts = risk_analyzer.analyze(venue, sim_state.crowd_state)

    # Filter by level if specified
    if level:
        alerts = [a for a in alerts if a.level == level]

    # Filter out acknowledged alerts
    alerts = [a for a in alerts if a.alert_id not in _acknowledged_alerts]

    return alerts


@router.get("/{event_id}/overview", response_model=AlertsOverview)
async def get_alerts_overview(event_id: str):
    """Get summary of alerts for dashboard."""
    alerts = await get_alerts(event_id)

    by_level = {}
    for level in AlertLevel:
        count = len([a for a in alerts if a.level == level])
        if count > 0:
            by_level[level.value] = count

    return AlertsOverview(
        total_active=len(alerts),
        by_level=by_level,
        recent_alerts=sorted(alerts, key=lambda a: a.priority)[:5]
    )


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Mark an alert as acknowledged."""
    _acknowledged_alerts.add(alert_id)
    return {"status": "acknowledged", "alert_id": alert_id}


@router.get("/{event_id}/recommendations", response_model=list[Recommendation])
async def get_recommendations(event_id: str):
    """Get AI-generated recommendations for an event."""
    from app.api.routes.simulation import _simulations

    if event_id not in _simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")

    sim_state = _simulations[event_id]
    scenario = SCENARIOS.get(sim_state.scenario)

    if not scenario:
        return []

    venue = load_venue(scenario["venue_id"])
    if not venue:
        return []

    recommender = RecommendationEngine()
    return recommender.generate(venue, sim_state.crowd_state)
