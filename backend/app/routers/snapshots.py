"""Snapshots router — Iceberg time-travel support."""

from fastapi import APIRouter, Query
import logging

from app.services.athena import AthenaService
from app.services.cache import CacheService
from app.models import SnapshotsResponse, DiffResponse, DiffRow, Snapshot
from app.utils.validation import validate_date, validate_snapshot_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.get("", response_model=SnapshotsResponse)
async def get_snapshots():
    """
    Get list of Iceberg snapshots with metadata.
    
    Each snapshot represents a version of the zone_report table.
    Snapshots are created when data is loaded via MERGE operations.
    
    Use snapshot_id with /zones endpoint for time-travel queries.
    """
    # Check cache (same for all calls, no params)
    cache = CacheService()
    cache_key = {}
    cached_result = cache.get("snapshots", cache_key)
    if cached_result is not None:
        logger.debug("Cache hit for snapshots")
        return cached_result
    
    # Query Athena
    athena = AthenaService()
    snapshot_records = athena.get_snapshots()
    
    # Transform to Snapshot models
    snapshots = []
    for record in snapshot_records:
        snapshot = Snapshot(
            snapshot_id=int(record.get("snapshot_id", 0)),
            committed_at=str(record.get("committed_at")),
            operation=record.get("operation"),
        )
        snapshots.append(snapshot)
    
    # Build response
    response = SnapshotsResponse(snapshots=snapshots)
    
    # Cache result (longer TTL since snapshots rarely change)
    cache.set("snapshots", cache_key, response, ttl_seconds=600)
    
    return response


@router.get("/diff", response_model=DiffResponse)
async def get_diff(
    from_snapshot_id: int = Query(..., description="Source snapshot ID"),
    to_snapshot_id: int = Query(..., description="Target snapshot ID"),
    data_as_of: str = Query(..., description="Date in YYYY-MM-DD format"),
):
    """
    Get rows that changed between two snapshots (Iceberg time-travel diff).
    
    Shows what changed in zone metrics between two data ingests.
    Useful for auditing data corrections and extraction revisions.
    
    Returns only rows where values differ between snapshots.
    """
    # Validate inputs
    from_snapshot_id = validate_snapshot_id(from_snapshot_id)
    to_snapshot_id = validate_snapshot_id(to_snapshot_id)
    data_as_of = validate_date(data_as_of)
    
    # Check cache
    cache = CacheService()
    cache_key = {
        "from_snapshot_id": from_snapshot_id,
        "to_snapshot_id": to_snapshot_id,
        "data_as_of": data_as_of
    }
    cached_result = cache.get("diff", cache_key)
    if cached_result is not None:
        logger.debug(f"Cache hit for diff: {from_snapshot_id} → {to_snapshot_id}")
        return cached_result
    
    # Query Athena
    athena = AthenaService()
    diff_records = athena.get_diff(from_snapshot_id, to_snapshot_id, data_as_of)
    
    # Transform to DiffRow models
    changes = []
    for record in diff_records:
        row = DiffRow(
            zone_key=record.get("zone_key"),
            health_zone=record.get("health_zone"),
            province=record.get("province"),
            data_as_of=str(record.get("data_as_of")),
            old_cases_cum=record.get("old_cases_cum"),
            new_cases_cum=record.get("new_cases_cum"),
            old_deaths_cum=record.get("old_deaths_cum"),
            new_deaths_cum=record.get("new_deaths_cum"),
        )
        changes.append(row)
    
    # Build response
    response = DiffResponse(
        from_snapshot_id=from_snapshot_id,
        to_snapshot_id=to_snapshot_id,
        changes=changes
    )
    
    # Cache result
    cache.set("diff", cache_key, response, ttl_seconds=600)
    
    return response
