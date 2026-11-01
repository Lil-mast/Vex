"""Query parameter validation for Vex API."""

import re
from typing import Optional
from app.exceptions import ValidationError


# Allowed values for parameterized queries
ALLOWED_METRICS = {"cases_cum", "cases_new_7d", "deaths_cum", "cfr"}
ALLOWED_EVENT_TYPES = {
    "imported_case",
    "exported_case",
    "medevac",
    "outbreak_declared",
    "outbreak_ended",
}
ALLOWED_COUNTRIES = {
    "DRC",
    "Uganda",
    "Kenya",
    "Nigeria",
    "Rwanda",
    "South Sudan",
}


def validate_metric(metric: str) -> str:
    """Validate that metric is in allowed list."""
    if metric not in ALLOWED_METRICS:
        raise ValidationError(
            f"Invalid metric '{metric}'. Must be one of: {', '.join(ALLOWED_METRICS)}"
        )
    return metric


def validate_date(date_str: str) -> str:
    """Validate date format (YYYY-MM-DD)."""
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(pattern, date_str):
        raise ValidationError(f"Invalid date format '{date_str}'. Must be YYYY-MM-DD")
    return date_str


def validate_province(province: Optional[str]) -> Optional[str]:
    """Validate province name (basic check for SQL injection)."""
    if province is None:
        return None
    if len(province) > 100:
        raise ValidationError("Province name too long")
    # Allow alphanumeric, spaces, hyphens
    if not re.match(r"^[\w\s\-]+$", province):
        raise ValidationError(f"Invalid province name '{province}'")
    return province


def validate_zone_key(zone_key: str) -> str:
    """Validate zone_key format (slug format: lowercase, hyphens)."""
    pattern = r"^[a-z0-9\-]+$"
    if not re.match(pattern, zone_key):
        raise ValidationError(f"Invalid zone_key '{zone_key}'. Must be lowercase with hyphens")
    return zone_key


def validate_country(country: str) -> str:
    """Validate country is in allowed list."""
    if country not in ALLOWED_COUNTRIES:
        raise ValidationError(
            f"Invalid country '{country}'. Must be one of: {', '.join(ALLOWED_COUNTRIES)}"
        )
    return country


def validate_snapshot_id(snapshot_id: int) -> int:
    """Validate snapshot ID is a positive integer."""
    if snapshot_id <= 0:
        raise ValidationError("Snapshot ID must be a positive integer")
    return snapshot_id


def validate_boolean(value: Optional[bool]) -> Optional[bool]:
    """Validate boolean parameter."""
    return value


def escape_sql_string(value: str) -> str:
    """Escape SQL string literals (basic protection)."""
    return value.replace("'", "''")
