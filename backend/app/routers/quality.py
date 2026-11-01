"""Quality router — data quality metrics."""

from fastapi import APIRouter, Query
import logging

from app.services.athena import AthenaService
from app.services.cache import CacheService
from app.models import QualityMetrics, ReportQuality
from app.utils.validation import validate_date

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quality", tags=["quality"])


@router.get("", response_model=QualityMetrics)
async def get_quality(
    data_as_of: str = Query(..., description="Date in YYYY-MM-DD format"),
):
    """
    Get data quality metrics for a specific date.
    
    Includes:
    - unassigned_cases: Cases with no health zone assigned
    - unassigned_share: Fraction of total cases that are unassigned (0-1)
    - reports: Validation status per report (rules passed, failed, confidence)
    
    Shows data confidence and any issues in the current dataset.
    """
    # Validate input
    data_as_of = validate_date(data_as_of)
    
    # Check cache
    cache = CacheService()
    cache_key = {"data_as_of": data_as_of}
    cached_result = cache.get("quality", cache_key)
    if cached_result is not None:
        logger.debug(f"Cache hit for quality: {data_as_of}")
        return cached_result
    
    # Query Athena
    athena = AthenaService()
    quality_data = athena.get_quality_metrics(data_as_of)
    
    # Transform to ReportQuality models
    reports = []
    for record in quality_data.get("reports", []):
        report = ReportQuality(
            report_id=record.get("report_id"),
            rules_passed=int(record.get("rules_passed", 0)),
            rules_failed=int(record.get("rules_failed", 0)),
            confidence=float(record.get("confidence", 0.0)),
        )
        reports.append(report)
    
    # Build response
    response = QualityMetrics(
        data_as_of=data_as_of,
        unassigned_cases=int(quality_data.get("unassigned_cases", 0)),
        unassigned_share=float(quality_data.get("unassigned_share", 0.0)),
        reports=reports
    )
    
    # Cache result
    cache.set("quality", cache_key, response, ttl_seconds=300)
    
    return response
