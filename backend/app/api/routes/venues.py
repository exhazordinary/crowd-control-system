"""Venue API routes."""

from fastapi import APIRouter, HTTPException

from app.models.venue import VenueResponse, VenueDetailResponse
from app.data.loader import load_venue, load_all_venues

router = APIRouter(prefix="/venues", tags=["venues"])


@router.get("", response_model=list[VenueResponse])
async def list_venues():
    """Get all available Malaysian venues."""
    venues = load_all_venues()
    return [
        VenueResponse(
            venue_id=v.venue_id,
            name=v.name,
            venue_type=v.venue_type,
            total_capacity=v.total_capacity,
            location=v.location
        )
        for v in venues
    ]


@router.get("/{venue_id}", response_model=VenueDetailResponse)
async def get_venue(venue_id: str):
    """Get venue details including zones and gates."""
    venue = load_venue(venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail=f"Venue {venue_id} not found")
    return venue


@router.get("/{venue_id}/zones")
async def get_venue_zones(venue_id: str):
    """Get all zones for a venue."""
    venue = load_venue(venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail=f"Venue {venue_id} not found")
    return venue.zones


@router.get("/{venue_id}/gates")
async def get_venue_gates(venue_id: str):
    """Get all gates for a venue."""
    venue = load_venue(venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail=f"Venue {venue_id} not found")
    return venue.gates
