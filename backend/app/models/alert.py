"""Alert and recommendation models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertCategory(str, Enum):
    DENSITY = "density"
    QUEUE = "queue"
    FLOW = "flow"
    CAPACITY = "capacity"
    SAFETY = "safety"
    TRANSPORT = "transport"


class Alert(BaseModel):
    """Alert for event staff."""
    alert_id: str
    event_id: str
    timestamp: datetime
    level: AlertLevel
    category: AlertCategory
    zone_id: Optional[str] = None
    gate_id: Optional[str] = None
    title: str
    message: str
    suggested_actions: list[str] = Field(default_factory=list)
    is_acknowledged: bool = False
    auto_dismiss: bool = False
    dismiss_after_minutes: Optional[float] = None

    @property
    def priority(self) -> int:
        """Numeric priority for sorting (lower = more urgent)."""
        priorities = {
            AlertLevel.EMERGENCY: 0,
            AlertLevel.CRITICAL: 1,
            AlertLevel.WARNING: 2,
            AlertLevel.INFO: 3,
        }
        return priorities.get(self.level, 4)


class Recommendation(BaseModel):
    """AI-generated recommendation for event staff."""
    recommendation_id: str
    event_id: str
    timestamp: datetime
    category: str  # gate, timing, routing, capacity
    title: str
    description: str
    impact: str  # e.g., "Reduces queue by ~30%"
    affected_zones: list[str] = Field(default_factory=list)
    affected_gates: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, description="AI confidence score")
    is_applied: bool = False

    # For display
    icon: str = "lightbulb"  # lucide icon name


class AlertResponse(Alert):
    """API response for alert."""
    pass


class RecommendationResponse(Recommendation):
    """API response for recommendation."""
    pass


class AlertsOverview(BaseModel):
    """Summary of alerts for dashboard."""
    total_active: int
    by_level: dict[str, int]  # {emergency: 1, critical: 2, ...}
    recent_alerts: list[Alert]
