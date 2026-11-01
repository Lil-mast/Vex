"""Zones router — health zone data with choropleth metrics."""

from typing import Optional
from fastapi import APIRouter, Query
import logging

from app.services.athena import AthenaService
from app.services.cache import CacheService
from app.models import ZonesResponse, TimeseriesResponse, GeoJSONFeature, TimeseriesPoint
from app.utils.validation import (
    validate_date, validate_metric, validate_province, validate_zone_key
)
from app.utils.transform import zone_to_feature
from app.exceptions import NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("", response_model=ZonesResponse)
async def get_zones(
    data_as_of: str = Query(..., description="Date in YYYY-MM-DD format"),
    metric: str = Query("cases_cum", description="cases_cum, cases_new_7d, deaths_cum, or cfr"),
    province: Optional[str] = Query(None, description="Optional province filter"),
    active_21d: bool = Query(False, description="Only zones with cases in last 21 days"),
    snapshot_id: Optional[int] = Query(None, description="Optional Iceberg snapshot ID for time travel"),
):
    """
    Get health zone choropleth data for a specific date.
    
    Returns GeoJSON FeatureCollection with zone polygons and metrics.
    Supports snapshot time-travel to view historical data revisions.
    """
    # Validate inputs
    data_as_of = validate_date(data_as_of)
    metric = validate_metric(metric)
    province = validate_province(province) if province else None
    
    # Check cache
    cache = CacheService()
    cache_key = {
        "data_as_of": data_as_of,
        "metric": metric,
        "province": province,
        "active_21d": active_21d,
        "snapshot_id": snapshot_id
    }
    cached_result = cache.get("zones", cache_key)
    if cached_result is not None:
        logger.debug(f"Cache hit for zones: {data_as_of}")
        return cached_result
    
    # Query Athena
    athena = AthenaService()
    zone_records = athena.get_zones_for_date(
        data_as_of=data_as_of,
        metric=metric,
        province=province,
        active_21d=active_21d,
        snapshot_id=snapshot_id
    )
    
    if not zone_records:
        logger.warning(f"No zones found for {data_as_of}")
    
    # Transform to GeoJSON Features
    features = []
    for zone in zone_records:
        # TODO: In Piece 4, fetch boundary geometry from boundaries service
        # For now, use placeholder Point geometry
        geometry = {
            "type": "Point",
            "coordinates": [0, 0]
        }
        feature = zone_to_feature(zone, geometry)
        features.append(feature)
    
    # Build response
    response = ZonesResponse(
        type="FeatureCollection",
        features=features
    )
    
    # Cache result
    cache.set("zones", cache_key, response, ttl_seconds=300)
    
    return response


@router.get("/{zone_key}/timeseries", response_model=TimeseriesResponse)
async def get_zone_timeseries(
    zone_key: str = Query(..., description="Zone key (e.g., 'bunia')"),
):
    """
    Get historical timeseries for a single zone.
    
    Returns all dates and metrics for this zone, sorted oldest to newest.
    """
    # Validate input
    zone_key = validate_zone_key(zone_key)
    
    # Check cache
    cache = CacheService()
    cache_key = {"zone_key": zone_key}
    cached_result = cache.get("zone_timeseries", cache_key)
    if cached_result is not None:
        logger.debug(f"Cache hit for timeseries: {zone_key}")
        return cached_result
    
    # Query Athena
    athena = AthenaService()
    timeseries_records = athena.get_zone_timeseries(zone_key)
    
    if not timeseries_records:
        raise NotFoundError(f"No timeseries found for zone '{zone_key}'")
    
    # Transform to TimeseriesResponse
    timeseries = []
    for record in timeseries_records:
        point = TimeseriesPoint(
            data_as_of=str(record.get("data_as_of")),
            cases_cum=int(record.get("cases_cum", 0)),
            deaths_cum=int(record.get("deaths_cum", 0)),
            cases_new_7d=record.get("cases_new_7d"),
            deaths_new_7d=record.get("deaths_new_7d"),
        )
        timeseries.append(point)
    
    # Build response
    response = TimeseriesResponse(
        zone_key=zone_key,
        timeseries=timeseries
    )
    
    # Cache result
    cache.set("zone_timeseries", cache_key, response, ttl_seconds=300)
    
    return response
