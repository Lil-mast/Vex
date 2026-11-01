# Vex Backend Design Document

## Overview

Vex backend is a FastAPI service that queries Apache Iceberg tables via AWS Athena, caches results, and serves them as GeoJSON and JSON responses. Built for the AWS Builder Center challenge.

**Region:** us-east-1  
**Python:** 3.12  
**Framework:** FastAPI + Pydantic v2  
**Data:** Athena + Iceberg + S3  
**Deploy:** AWS Lambda (via `mangum`)

---

## Architecture Diagram

```
HTTP Request
    ↓
FastAPI Router (validates params)
    ↓
Query Parameter Validators (allow-lists, regex)
    ↓
Cache.get() → Memory? → S3? → Query Athena?
    ↓
AthenaService.execute_query() (parameterized, safe)
    ↓
awswrangler → Athena engine v3
    ↓
Results (List[Dict])
    ↓
Cache.set() (memory + S3)
    ↓
Transform.zone_to_feature() (for GeoJSON endpoints)
    ↓
Pydantic Model Validation & Serialization
    ↓
JSON Response (with proper status code)
    ↓
HTTP Response
```

---

## Module Breakdown

### Core Application (`app/`)

#### `main.py`
- FastAPI app initialization
- CORS middleware (allow all for dev; restrict in production)
- Global exception handlers (custom `VexError` → structured `{error, detail}` response)
- Health check endpoint (`GET /health`)
- Router inclusion points (routers/ modules)

**Key Features:**
- Async-ready for Lambda
- Exception handler maps custom exceptions to HTTP status codes
- Logging on all errors

#### `exceptions.py`
Custom exception hierarchy:
- `VexError` (base, 500)
- `ValidationError` (400)
- `AthenaError` (500)
- `AthenaTimeoutError` (500)
- `NotFoundError` (404)
- `ConfigError` (500)

Each carries `message` and `status_code` for proper HTTP responses.

#### `models.py`
Pydantic v2 response models (15+):

| Endpoint | Model |
|---|---|
| `/health` | `HealthResponse` |
| `/dates` | `DatesResponse` with list of `DateWithStatus` |
| `/zones` | `ZonesResponse` (GeoJSON FeatureCollection) |
| `/zones/{zone_key}/timeseries` | `TimeseriesResponse` with list of `TimeseriesPoint` |
| `/countries` | `CountriesResponse` with list of `CountryDataPoint` |
| `/kenya/counties` | `KenyaCountiesResponse` (GeoJSON FeatureCollection) |
| `/events` | `EventsResponse` with list of `Event` |
| `/quality` | `QualityMetrics` with `unassigned_cases`, `unassigned_share`, `reports[]` |
| `/snapshots` | `SnapshotsResponse` with list of `Snapshot` |
| `/diff` | `DiffResponse` with list of `DiffRow` |

All models include proper type hints and optional fields where data may be null.

### Services Layer (`app/services/`)

#### `athena.py` — AthenaService
Query execution against Athena/Iceberg tables.

**Constructor:**
- Reads `AWS_REGION`, `GLUE_DATABASE`, `ATHENA_WORKGROUP`, `ATHENA_RESULTS_BUCKET` from env
- Initializes `boto3` Athena and S3 clients
- Raises `ConfigError` if required env vars missing

**Public Methods:**

1. **`execute_query(query: str, timeout_seconds: int) → List[Dict]`**
   - Core method: executes parameterized SQL via `awswrangler`
   - Uses `read_sql_query()` for simplified query execution
   - Returns results as list of dicts (one dict per row)
   - Catches `TimeoutError` → `AthenaTimeoutError`
   - Catches `ClientError` → `AthenaError` with Athena error code

2. **`get_latest_date() → Optional[str]`**
   - Latest `data_as_of` from `zone_report` table
   - Used to default API queries to "today"

3. **`get_dates() → List[Dict]`**
   - Returns all distinct `data_as_of` dates with:
     - `reports_count` — total reports for that date
     - `validation_passed` — count of validated=true rows
     - `validation_failed` — count of validated=false rows
   - Sorted DESC by date (newest first)

4. **`get_zones_for_date(date, metric, province, active_21d, snapshot_id) → List[Dict]`**
   - Core endpoint data
   - Filters:
     - `province` — exact match on province name
     - `active_21d` — only zones with `cases_new_7d > 0`
   - Snapshot support: `FOR VERSION AS OF {snapshot_id}` for time travel
   - Returns all metrics (cumulative, 7-day, CFR calculation)

5. **`get_zone_timeseries(zone_key) → List[Dict]`**
   - Historical progression of a single zone
   - All dates, all metrics
   - Sorted ASC by date (oldest first)

6. **`get_countries(date) → List[Dict]`**
   - Country-level case/death totals from `country_report` table
   - DRC, Uganda, Kenya, Nigeria, etc.

7. **`get_kenya_counties(date) → List[Dict]`**
   - Kenya only: zone data aggregated to county level
   - From `zone_report` where `country = 'Kenya'`

8. **`get_events(date, country) → List[Dict]`**
   - Curated events (imports, exports, medevacs) up to date
   - Optional country filter

9. **`get_quality_metrics(date) → Dict`**
   - Unassigned case count and share
   - Per-report validation stats:
     - `rules_passed` — count of validated=true
     - `rules_failed` — count of validated=false
     - `confidence` — average extraction_confidence

10. **`get_snapshots() → List[Dict]`**
    - List from `$snapshots` metadata table
    - Each: `snapshot_id`, `committed_at`, `operation`

11. **`get_diff(from_snap, to_snap, date) → List[Dict]`**
    - FULL OUTER JOIN between two snapshots
    - Returns rows where values changed:
      - `zone_key`, `health_zone`, `province`, `data_as_of`
      - `old_cases_cum`, `new_cases_cum`, `old_deaths_cum`, `new_deaths_cum`

#### `cache.py` — CacheService
2-tier caching: in-memory + S3.

**Constructor:**
- Initializes empty in-memory cache dict
- Reads `LAKE_BUCKET` from env
- Sets default TTL to 300 seconds (5 min)

**Public Methods:**

1. **`get(endpoint, params) → Optional[Any]`**
   - Checks in-memory cache first
   - If expired, removes it
   - Falls back to S3 if available
   - Restores S3 cache to memory on hit
   - Returns None if not found

2. **`set(endpoint, params, result, ttl_seconds)`**
   - Stores to in-memory cache with expiry time
   - Stores to S3 as JSON with expiry metadata
   - Failures on S3 write don't block response (logged as warning)

3. **`clear(endpoint)`**
   - Clears all or specific endpoint cache
   - In-memory only (S3 expires naturally)

**Cache Key Generation:**
- `SHA256(json.dumps(params, sort_keys=True))`
- Combined with endpoint name: `{endpoint}:{hash}`
- S3 path: `cache/{endpoint}:{hash}.json`

### Utils Layer (`app/utils/`)

#### `validation.py`
Parameterized query validation with allow-lists.

**Allow-lists (prevent SQL injection + enforce API contract):**
```python
ALLOWED_METRICS = {"cases_cum", "cases_new_7d", "deaths_cum", "cfr"}
ALLOWED_EVENT_TYPES = {"imported_case", "exported_case", "medevac", ...}
ALLOWED_COUNTRIES = {"DRC", "Uganda", "Kenya", "Nigeria", "Rwanda", "South Sudan"}
```

**Validators:**
- `validate_metric(str) → str` — Must be in ALLOWED_METRICS
- `validate_date(str) → str` — Must match YYYY-MM-DD
- `validate_province(str) → str` — Max 100 chars, alphanumeric/spaces/hyphens
- `validate_zone_key(str) → str` — Lowercase with hyphens only
- `validate_country(str) → str` — Must be in ALLOWED_COUNTRIES
- `validate_snapshot_id(int) → int` — Positive integer
- `escape_sql_string(str) → str` — Replace `'` with `''` (basic escaping)

All raise `ValidationError` with descriptive message on failure.

#### `transform.py`
Transform Athena results into response models.

**Functions:**
- `zone_to_feature(zone_data, geometry) → Dict` — Convert zone record to GeoJSON Feature
  - Handles null metrics gracefully
  - CFR calculated if cases > 0, else null
  - Default Point geometry if none provided

- `calculate_cfr(cases, deaths) → Optional[float]` — Case fatality rate
  - `deaths / cases` if cases > 0, else None

- `format_date(date_val) → str` — Convert to YYYY-MM-DD

- `normalize_numeric(value, default) → int` — Null-safe int conversion

### Routers (`app/routers/`) — To Be Created

Each router will:
1. Define FastAPI `@app.get()` or `@app.post()` routes
2. Validate query/path params using `validation.py`
3. Call `AthenaService` methods
4. Cache results via `CacheService`
5. Transform to response model
6. Return with proper status code

**Planned Routers:**
- `health.py` — `/health` (already in main.py, can move here)
- `zones.py` — `/zones`, `/zones/{zone_key}/timeseries`
- `countries.py` — `/countries`, `/kenya/counties`
- `events.py` — `/events`
- `snapshots.py` — `/snapshots`, `/diff`
- `quality.py` — `/quality`

---

## Data Flow Example: GET /zones

```
Client: GET /zones?data_as_of=2026-10-20&metric=cases_cum&province=Ituri

↓ FastAPI Router

validation.validate_date("2026-10-20") → OK
validation.validate_metric("cases_cum") → OK
validation.validate_province("Ituri") → OK

↓ Cache Check

cache.get("zones", {data_as_of: "2026-10-20", metric: "cases_cum", province: "Ituri"})
→ Check memory: expired or miss
→ Check S3: miss
→ Return None

↓ Athena Query

athena.get_zones_for_date(
  "2026-10-20",
  "cases_cum",
  "Ituri",
  active_21d=False,
  snapshot_id=None
)

↓ AthenaService

execute_query(
  """SELECT ... FROM zone_report WHERE data_as_of = '2026-10-20' AND province = 'Ituri' ..."""
)

↓ awswrangler + Athena

Athena engine v3 queries Iceberg table → 12 zone rows returned as DataFrame

↓ Transform

df.to_dict(orient="records") → List[Dict]

[
  {zone_key: "bunia", health_zone: "Bunia", province: "Ituri", cases_cum: 145, ...},
  {zone_key: "ariwara", health_zone: "Ariwara", province: "Ituri", cases_cum: 32, ...},
  ...
]

↓ Cache Set

cache.set("zones", {...}, results, ttl_seconds=300)
→ In-memory cache + S3 write

↓ Transform to Response

for zone in results:
  feature = transform.zone_to_feature(zone, geometry_from_boundaries)

features = [feature, feature, ...]

response = ZonesResponse(
  type="FeatureCollection",
  features=features
)

↓ Serialize

Pydantic serializes to JSON → FastAPI returns 200 OK with GeoJSON FeatureCollection

Client receives:
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {type: "Polygon", coordinates: [...]},
      "properties": {
        "zone_key": "bunia",
        "health_zone": "Bunia",
        "province": "Ituri",
        "cases_cum": 145,
        ...
      }
    },
    ...
  ]
}
```

---

## Error Handling

| Scenario | Exception | Status Code | Response |
|---|---|---|---|
| Invalid metric | `ValidationError` | 400 | `{error: "ValidationError", detail: "Invalid metric..."}` |
| Missing env var | `ConfigError` | 500 | `{error: "ConfigError", detail: "..."}` |
| Athena query fails | `AthenaError` | 500 | `{error: "AthenaError", detail: "Athena error X: ..."}` |
| Query times out | `AthenaTimeoutError` | 500 | `{error: "AthenaTimeoutError", detail: "Query timed out..."}` |
| Zone not found | `NotFoundError` | 404 | `{error: "NotFoundError", detail: "..."}` |
| Unexpected error | Exception (caught globally) | 500 | `{error: "InternalServerError", detail: "An unexpected error occurred"}` |

---

## Caching Strategy

**Why 2-tier?**
- Lambda containers are ephemeral; in-memory cache is lost between invocations
- S3 cache persists across container lifecycles
- Memory is fast (microseconds), S3 is slower (tens of ms) but still beats Athena (seconds)

**TTL (Time-To-Live):**
- Default: 300 seconds (5 minutes)
- Configurable per endpoint if needed
- After TTL, entry is considered expired and removed

**Cost Impact:**
- Reduces Athena scans significantly (same query within 5 min = cache hit)
- S3 write per unique query (minimal cost)
- Reduces Lambda execution time for common queries

**Invalidation:**
- Natural expiry (TTL)
- Manual via `cache.clear()` if data is refreshed out-of-band
- No explicit invalidation on Athena update (users see data within TTL window)

---

## Query Safety

All user inputs go through `validation.py` before use in SQL:

1. **Metrics** — allow-list only
2. **Dates** — regex pattern enforced
3. **Zone keys** — lowercase slug pattern
4. **Provinces** — max length + alphanumeric
5. **Countries** — allow-list only

SQL is built with:
- Parameterized queries (via f-strings with validated inputs, then executed by awswrangler)
- NO direct string concatenation of unsafe values
- `escape_sql_string()` as fallback for string literals

---

## Environment Configuration

| Variable | Default | Purpose |
|---|---|---|
| `AWS_REGION` | `us-east-1` | AWS region for all services |
| `GLUE_DATABASE` | `vex` | Glue database name |
| `ATHENA_WORKGROUP` | `vex` | Athena workgroup (must exist with scan limit set) |
| `ATHENA_RESULTS_BUCKET` | (required) | S3 bucket for Athena query results |
| `LAKE_BUCKET` | (optional) | S3 bucket for cache storage; if not set, cache only in memory |
| `VEX_LOCAL_FIXTURES` | `0` | If `1`, use fixtures from `data/fixtures/` instead of Athena |

---

## Next: Piece 3 — Routers

The routers will orchestrate services and handle HTTP concerns (query params, response codes, swagger docs).

Each router:
- Defines one or more endpoints
- Validates inputs
- Calls services
- Caches
- Returns typed response

Example structure for `routers/zones.py`:

```python
from fastapi import APIRouter, Query
from app.services.athena import AthenaService
from app.services.cache import CacheService
from app.utils.validation import validate_date, validate_metric, validate_province
from app.models import ZonesResponse

router = APIRouter(prefix="/zones", tags=["zones"])

@router.get("", response_model=ZonesResponse)
async def get_zones(
    data_as_of: str = Query(..., description="YYYY-MM-DD"),
    metric: str = Query("cases_cum", description="cases_cum, cases_new_7d, deaths_cum, cfr"),
    province: str = Query(None, description="Optional province filter"),
    active_21d: bool = Query(False, description="Only zones with cases in last 7 days"),
):
    # Validate
    data_as_of = validate_date(data_as_of)
    metric = validate_metric(metric)
    province = validate_province(province) if province else None
    
    # Cache check
    cache = CacheService()
    cached = cache.get("zones", {data_as_of, metric, province, active_21d})
    if cached:
        return cached
    
    # Query
    athena = AthenaService()
    zones = athena.get_zones_for_date(data_as_of, metric, province, active_21d)
    
    # Transform + cache
    features = [zone_to_feature(z, ...) for z in zones]
    response = ZonesResponse(features=features)
    cache.set("zones", {...}, response)
    
    return response
```

