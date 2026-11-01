"""Dates router — available dates and report metadata."""

from fastapi import APIRouter
import logging

from app.services.athena import AthenaService
from app.services.cache import CacheService
from app.models import DatesResponse, DateWithStatus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dates"])


@router.get("/dates", response_model=DatesResponse)
async def get_dates():
    """
    Get list of all available data_as_of dates.
    
    Includes for each date:
    - reports_count: Number of reports for that date
    - validation_passed: Count of validated (good quality) reports
    - validation_failed: Count of reports with validation issues
    
    Sorted newest to oldest.
    Useful for time slider in frontend.
    """
    # Check cache (same for all calls)
    cache = CacheService()
    cache_key = {}
    cached_result = cache.get("dates", cache_key)
    if cached_result is not None:
        logger.debug("Cache hit for dates")
        return cached_result
    
    # Query Athena
    athena = AthenaService()
    date_records = athena.get_dates()
    
    # Transform to DateWithStatus models
    dates = []
    for record in date_records:
        date_status = DateWithStatus(
            data_as_of=str(record.get("data_as_of")),
            reports_count=int(record.get("reports_count", 0)),
            validation_passed=int(record.get("validation_passed", 0)),
            validation_failed=int(record.get("validation_failed", 0)),
        )
        dates.append(date_status)
    
    # Build response
    response = DatesResponse(dates=dates)
    
    # Cache result (longer TTL since dates rarely change)
    cache.set("dates", cache_key, response, ttl_seconds=600)
    
    return response
