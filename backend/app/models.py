"""Pydantic models for Vex API responses."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Health & Meta
class HealthResponse(BaseModel):
    """Response for GET /health."""
    status: str = "ok"
    version: str = "0.1.0"


# Error responses
class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str
    detail: str


# Dates
class DateWithStatus(BaseModel):
    """A data_as_of date with report validation status."""
    data_as_of: str  # YYYY-MM-DD
    reports_count: int
    validation_passed: int
    validation_failed: int


class DatesResponse(BaseModel):
    """Response for GET /dates."""
    dates: List[DateWithStatus]


# GeoJSON Feature
class GeoJSONPoint(BaseModel):
    """GeoJSON Point geometry."""
    type: str = "Point"
    coordinates: List[float]  # [lon, lat]


class GeoJSONPolygon(BaseModel):
    """GeoJSON Polygon geometry."""
    type: str = "Polygon"
    coordinates: List[List[List[float]]]


class GeoJSONFeatureProperties(BaseModel):
    """Properties for a zone feature."""
    zone_key: str
    health_zone: str
    province: str
    country: str
    cases_cum: int
    deaths_cum: int
    cases_new_7d: Optional[int] = None
    deaths_new_7d: Optional[int] = None
    cfr: Optional[float] = None  # case fatality rate
    first_confirmed: Optional[str] = None  # YYYY-MM-DD
    last_case_date: Optional[str] = None  # YYYY-MM-DD
    validated: bool
    unassigned: bool = False


class GeoJSONFeature(BaseModel):
    """A single GeoJSON feature (zone)."""
    type: str = "Feature"
    geometry: Dict[str, Any]  # Point or Polygon
    properties: GeoJSONFeatureProperties


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection response."""
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]


# Zones
class ZonesResponse(GeoJSONFeatureCollection):
    """Response for GET /zones."""
    pass


# Timeseries
class TimeseriesPoint(BaseModel):
    """A single point in a zone's timeseries."""
    data_as_of: str  # YYYY-MM-DD
    cases_cum: int
    deaths_cum: int
    cases_new_7d: Optional[int] = None
    deaths_new_7d: Optional[int] = None


class TimeseriesResponse(BaseModel):
    """Response for GET /zones/{zone_key}/timeseries."""
    zone_key: str
    timeseries: List[TimeseriesPoint]


# Countries
class CountryDataPoint(BaseModel):
    """Country-level case/death data."""
    country: str
    cases_cum: int
    deaths_cum: int


class CountriesResponse(BaseModel):
    """Response for GET /countries."""
    data_as_of: str
    countries: List[CountryDataPoint]


# Kenya Counties
class KenyaCountyProperties(BaseModel):
    """Properties for a Kenya county feature."""
    county: str
    cases_cum: int


class KenyaCountyFeature(BaseModel):
    """A single Kenya county feature."""
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: KenyaCountyProperties


class KenyaCountiesResponse(BaseModel):
    """Response for GET /kenya/counties."""
    type: str = "FeatureCollection"
    features: List[KenyaCountyFeature]


# Events
class Event(BaseModel):
    """A curated event (import, export, etc.)."""
    event_id: str
    event_date: str  # YYYY-MM-DD
    country: str
    admin1: Optional[str] = None
    event_type: str  # imported_case, exported_case, medevac, outbreak_declared, outbreak_ended
    description: str
    source_url: str


class EventsResponse(BaseModel):
    """Response for GET /events."""
    data_as_of: str
    events: List[Event]


# Quality
class ReportQuality(BaseModel):
    """Quality metrics for a single report."""
    report_id: str
    rules_passed: int
    rules_failed: int
    confidence: float  # 0-1


class QualityMetrics(BaseModel):
    """Response for GET /quality."""
    data_as_of: str
    unassigned_cases: int
    unassigned_share: float  # 0-1
    reports: List[ReportQuality]


# Snapshots
class Snapshot(BaseModel):
    """An Iceberg snapshot."""
    snapshot_id: int
    committed_at: str  # ISO timestamp
    operation: str  # append, replace, overwrite


class SnapshotsResponse(BaseModel):
    """Response for GET /snapshots."""
    snapshots: List[Snapshot]


# Diff
class DiffRow(BaseModel):
    """A row that changed between two snapshots."""
    zone_key: str
    health_zone: str
    province: str
    data_as_of: str
    old_cases_cum: Optional[int] = None
    new_cases_cum: Optional[int] = None
    old_deaths_cum: Optional[int] = None
    new_deaths_cum: Optional[int] = None


class DiffResponse(BaseModel):
    """Response for GET /diff."""
    from_snapshot_id: int
    to_snapshot_id: int
    changes: List[DiffRow]
