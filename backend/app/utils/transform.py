"""Transform Athena results into response models."""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def zone_to_feature(
    zone_data: Dict[str, Any],
    geometry: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convert a zone record from Athena into a GeoJSON Feature.
    
    Args:
        zone_data: Raw zone data from Athena
        geometry: Optional GeoJSON geometry (Point or Polygon from boundary data)
        
    Returns:
        GeoJSON Feature dict
    """
    # Default to Point geometry if none provided
    if geometry is None:
        geometry = {
            "type": "Point",
            "coordinates": [0, 0]  # Placeholder
        }

    cfr = zone_data.get("cfr")
    if cfr is not None:
        cfr = round(cfr, 4)

    properties = {
        "zone_key": zone_data.get("zone_key"),
        "health_zone": zone_data.get("health_zone"),
        "province": zone_data.get("province"),
        "country": zone_data.get("country"),
        "cases_cum": int(zone_data.get("cases_cum", 0)),
        "deaths_cum": int(zone_data.get("deaths_cum", 0)),
        "cases_new_7d": zone_data.get("cases_new_7d"),
        "deaths_new_7d": zone_data.get("deaths_new_7d"),
        "cfr": cfr,
        "first_confirmed": zone_data.get("first_confirmed"),
        "last_case_date": zone_data.get("last_case_date"),
        "validated": bool(zone_data.get("validated", True)),
        "unassigned": bool(zone_data.get("is_unassigned", False)),
    }

    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": properties
    }


def calculate_cfr(cases: int, deaths: int) -> Optional[float]:
    """Calculate case fatality rate."""
    if cases > 0:
        return round(deaths / cases, 4)
    return None


def format_date(date_val: Any) -> str:
    """Format date to YYYY-MM-DD string."""
    if date_val is None:
        return None
    return str(date_val)


def normalize_numeric(value: Any, default: int = 0) -> int:
    """Normalize numeric values, handle nulls."""
    if value is None:
        return default
    return int(value)
