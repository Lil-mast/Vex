"""Events router — curated import/export/medevac events."""

from typing import Optional
from fastapi import APIRouter, Query
import logging

from app.services.athena import AthenaService
from app.services.cache import CacheService
from app.models import EventsResponse, Event
from app.utils.validation import validate_date, validate_country

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventsResponse)
async def get_events(
    data_as_of: str = Query(..., description="Date in YYYY-MM-DD format (up to this date)"),
    country: Optional[str] = Query(None, description="Optional country filter (DRC, Uganda, Kenya, etc.)"),
):
    """
    Get curated events (imports, exports, medevacs, outbreak declarations/ends).
    
    Events are hand-sourced from official statements and include:
    - Imported cases (where disease was introduced from)
    - Exported cases (where disease spread to)
    - Medevac events
    - Outbreak declared / outbreak ended dates
    
    Events up to data_as_of are included.
    """
    # Validate inputs
    data_as_of = validate_date(data_as_of)
    if country:
        country = validate_country(country)
    
    # Check cache
    cache = CacheService()
    cache_key = {
        "data_as_of": data_as_of,
        "country": country
    }
    cached_result = cache.get("events", cache_key)
    if cached_result is not None:
        logger.debug(f"Cache hit for events: {data_as_of}")
        return cached_result
    
    # Query Athena
    athena = AthenaService()
    event_records = athena.get_events(data_as_of, country)
    
    # Transform to Event models
    events = []
    for record in event_records:
        event = Event(
            event_id=record.get("event_id"),
            event_date=str(record.get("event_date")),
            country=record.get("country"),
            admin1=record.get("admin1"),
            event_type=record.get("event_type"),
            description=record.get("description"),
            source_url=record.get("source_url"),
        )
        events.append(event)
    
    # Build response
    response = EventsResponse(
        data_as_of=data_as_of,
        events=events
    )
    
    # Cache result
    cache.set("events", cache_key, response, ttl_seconds=300)
    
    return response
