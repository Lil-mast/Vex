# Vex Backend Architecture Layers

## Layer Stack (Bottom to Top)

```
┌─────────────────────────────────────────────────┐
│  HTTP / Client Layer                            │
│  (Browser, Frontend, Mobile)                    │
└─────────────────────────┬───────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────┐
│  FastAPI Router Layer                           │
│  (app/routers/*.py)                             │
│  - Route matching (@app.get, @app.post)         │
│  - Query param binding                          │
│  - OpenAPI docs generation                      │
└─────────────────────────┬───────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────┐
│  Validation Layer                               │
│  (app/utils/validation.py)                      │
│  - Allow-list enforcement                       │
│  - Regex pattern matching                       │
│  - Type coercion & error messages               │
└─────────────────────────┬───────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────┐
│  Business Logic Layer                           │
│  (app/services/*.py)                            │
│  - AthenaService (queries)                      │
│  - CacheService (memory + S3)                   │
│  - Error handling & retry logic                 │
└─────────────────────────┬───────────────────────┘
                          │
            ┌─────────────┼─────────────┐
            │             │             │
            ↓             ↓             ↓
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │ AWS Clients  │  │   Transform  │  │ Model Valid. │
   │ (boto3)      │  │ (transform.py)   │ (pydantic)   │
   │              │  │              │  │              │
   │ - Athena     │  │ - GeoJSON    │  │ - Serialize  │
   │ - S3         │  │ - CFR calc   │  │ - Schema     │
   │ - Glue       │  │ - Date fmt   │  │ - Type check │
   └──────────────┘  └──────────────┘  └──────────────┘
            │             │             │
            └─────────────┼─────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────┐
│  AWS Backend Layer                              │
│  - Apache Iceberg tables (S3)                   │
│  - Athena query engine (v3)                     │
│  - AWS Glue metadata catalog                    │
│  - S3 storage & caching                         │
└─────────────────────────────────────────────────┘
```

---

## Data Flow by Endpoint Type

### Query Endpoints (GET /zones, /countries, etc.)

```
Client Request
    ↓
FastAPI Router
    ├─ Extract query params
    ├─ Call Validator
    │   ├─ Check allow-lists (metric, country)
    │   ├─ Validate format (date, zone_key)
    │   └─ Raise ValidationError if invalid
    │
    ├─ CacheService.get()
    │   ├─ Check in-memory cache
    │   │   └─ If hit & not expired → return result
    │   ├─ Check S3 cache
    │   │   └─ If hit & not expired → return result
    │   └─ Return None if miss
    │
    ├─ If cache miss: AthenaService.execute_query()
    │   ├─ Build parameterized SQL query
    │   ├─ Call awswrangler.athena.read_sql_query()
    │   │   └─ Athena executes → Iceberg table scanned
    │   ├─ Convert DataFrame → List[Dict]
    │   └─ Catch errors (timeout, query fail)
    │
    ├─ Transform.zone_to_feature() or similar
    │   ├─ Convert each row to proper format
    │   ├─ Merge with boundary geometry (for GeoJSON)
    │   ├─ Calculate CFR if needed
    │   └─ Handle nulls gracefully
    │
    ├─ CacheService.set()
    │   ├─ Store in memory with TTL
    │   ├─ Store to S3 (async-friendly)
    │   └─ Log any failures (non-blocking)
    │
    ├─ Pydantic Model validation
    │   ├─ Validate response shape
    │   ├─ Type coercion (int, float, bool)
    │   ├─ Optional field checks
    │   └─ Serialize to JSON
    │
    └─ Return 200 OK + JSON response

    ↓
Client Response (JSON or GeoJSON)
```

### Snapshot/Time-Travel Endpoints (GET /snapshots, /diff)

```
GET /snapshots
    ↓
AthenaService.get_snapshots()
    ├─ Query: SELECT * FROM zone_report$snapshots
    ├─ Iceberg metadata table (no data scan)
    └─ Return: [snapshot_id, committed_at, operation, ...]
    ↓
Return: SnapshotsResponse

GET /diff?from_snapshot={id1}&to_snapshot={id2}
    ↓
AthenaService.get_diff(id1, id2)
    ├─ Query: SELECT ... FROM zone_report FOR VERSION AS OF {id1}
    ├─ FULL OUTER JOIN with zone_report FOR VERSION AS OF {id2}
    ├─ Return rows where values changed
    └─ Compare old vs new metrics per zone
    ↓
Return: DiffResponse with [DiffRow, DiffRow, ...]
```

---

## Request Lifecycle (Detailed)

### Step 1: Request Arrives

```
GET /zones?data_as_of=2026-10-20&metric=cases_cum&province=Ituri HTTP/1.1
Host: api.vex.example.com
```

### Step 2: FastAPI Routing

- FastAPI matches `GET /zones` to `app/routers/zones.py::get_zones()`
- Extracts query params:
  - `data_as_of = "2026-10-20"`
  - `metric = "cases_cum"`
  - `province = "Ituri"`
  - `active_21d = False` (default)
  - `snapshot_id = None` (default)

### Step 3: Validation

```python
data_as_of = validate_date("2026-10-20")           # ✓ Matches YYYY-MM-DD
metric = validate_metric("cases_cum")              # ✓ In ALLOWED_METRICS
province = validate_province("Ituri")              # ✓ Alphanumeric + length check
active_21d = validate_boolean(False)               # ✓ Valid boolean
snapshot_id = validate_snapshot_id(None)           # ✓ None is OK
```

If any validation fails:
```python
raise ValidationError("Invalid metric 'invalid_metric'")
# Caught by global exception handler
# Returns: {"error": "ValidationError", "detail": "...", "status_code": 400}
```

### Step 4: Cache Lookup

```python
cache_key = cache._generate_cache_key("zones", {
    "data_as_of": "2026-10-20",
    "metric": "cases_cum",
    "province": "Ituri",
    "active_21d": False,
    "snapshot_id": None
})
# hash = SHA256(...) = "a1b2c3d4e5f6..."
# key = "zones:a1b2c3d4e5f6..."

# Check in-memory cache
if key in cache.in_memory_cache:
    cached_data = cache.in_memory_cache[key]
    if cached_data["expires_at"] > now():
        logger.debug(f"Cache hit: {key}")
        return cached_data["result"]
    else:
        del cache.in_memory_cache[key]  # Expired

# Check S3 cache
try:
    response = s3.get_object(Bucket="vex-lake-123", Key=f"cache/{key}.json")
    cached_data = json.loads(response["Body"].read())
    if cached_data["expires_at"] > now().isoformat():
        logger.debug(f"Cache hit (S3): {key}")
        cache.in_memory_cache[key] = {...}  # Restore to memory
        return cached_data["result"]
except NoSuchKey:
    pass  # Cache miss
```

If cache miss, proceed to Athena.

### Step 5: Athena Query

```python
query = f"""
SELECT
    zone_key, health_zone, province, country, cases_cum, deaths_cum,
    cases_new_7d, deaths_new_7d,
    CAST(deaths_cum AS FLOAT) / NULLIF(cases_cum, 0) as cfr,
    validated, is_unassigned, extraction_confidence
FROM vex.zone_report
WHERE data_as_of = '2026-10-20' AND province = 'Ituri'
ORDER BY health_zone
"""

# Execute via awswrangler
df = wr.athena.read_sql_query(
    sql=query,
    database="vex",
    s3_output="s3://vex-athena-123/",
    workgroup="vex"
)

# Convert to list of dicts
results = df.to_dict(orient="records")
# [
#   {"zone_key": "bunia", "health_zone": "Bunia", ..., "cases_cum": 145, ...},
#   {"zone_key": "ariwara", "health_zone": "Ariwara", ..., "cases_cum": 32, ...}
# ]
```

If query fails:
```python
except TimeoutError:
    raise AthenaTimeoutError("Query timed out after 30s")
except ClientError as e:
    raise AthenaError(f"Athena error: {e}")
```

### Step 6: Transform Results

```python
features = []
for zone in results:
    # Fetch boundary geometry (from boundaries.py service, to be created)
    geometry = boundaries.get_geometry(zone["zone_key"])
    
    # Convert to GeoJSON Feature
    feature = transform.zone_to_feature(zone, geometry)
    # {
    #   "type": "Feature",
    #   "geometry": {"type": "Polygon", "coordinates": [...]},
    #   "properties": {
    #     "zone_key": "bunia",
    #     "health_zone": "Bunia",
    #     "province": "Ituri",
    #     "cases_cum": 145,
    #     ...
    #   }
    # }
    features.append(feature)
```

### Step 7: Cache Result

```python
cache.set("zones", params_dict, features, ttl_seconds=300)

# In-memory
cache.in_memory_cache[key] = {
    "result": features,
    "expires_at": datetime.utcnow() + timedelta(seconds=300)
}

# S3
s3.put_object(
    Bucket="vex-lake-123",
    Key=f"cache/{key}.json",
    Body=json.dumps({
        "result": features,
        "expires_at": "2026-10-20T12:00:00",
        "cached_at": "2026-10-20T11:55:00"
    })
)
```

### Step 8: Build Response Model

```python
response = ZonesResponse(
    type="FeatureCollection",
    features=features
)

# Pydantic validates:
# - type must be "FeatureCollection"
# - features must be list of GeoJSONFeature
# - Each feature.properties must match GeoJSONFeatureProperties schema
# - All required fields present
# - All types correct
```

### Step 9: Serialize to JSON

```python
# Pydantic's model_dump() + FastAPI's JSONEncoder
json_response = response.model_dump(mode="json")
# {
#   "type": "FeatureCollection",
#   "features": [
#     {
#       "type": "Feature",
#       "geometry": {...},
#       "properties": {...}
#     },
#     ...
#   ]
# }
```

### Step 10: HTTP Response

```
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: public, max-age=300

{
  "type": "FeatureCollection",
  "features": [...]
}
```

---

## Error Paths

### Example 1: Invalid Metric

```
GET /zones?metric=invalid_metric

Validation:
  validate_metric("invalid_metric")
  → "invalid_metric" not in ALLOWED_METRICS
  → raise ValidationError("Invalid metric 'invalid_metric'. Must be...")

Exception Handler:
  @app.exception_handler(VexError)
  → status_code = 400 (from ValidationError.__init__)
  → return JSONResponse(status_code=400, content={
      "error": "ValidationError",
      "detail": "Invalid metric..."
    })

Response:
  HTTP/1.1 400 Bad Request
  {
    "error": "ValidationError",
    "detail": "Invalid metric 'invalid_metric'. Must be one of: cases_cum, cases_new_7d, deaths_cum, cfr"
  }
```

### Example 2: Athena Query Timeout

```
AthenaService.execute_query():
  wr.athena.read_sql_query(...) → TimeoutError
  → raise AthenaTimeoutError("Query timed out after 30s")

Exception Handler:
  @app.exception_handler(VexError)
  → status_code = 500 (from AthenaTimeoutError init)
  → return JSONResponse(status_code=500, content={
      "error": "AthenaTimeoutError",
      "detail": "Query timed out after 30s"
    })

Response:
  HTTP/1.1 500 Internal Server Error
  {
    "error": "AthenaTimeoutError",
    "detail": "Query timed out after 30s"
  }
```

### Example 3: Missing Environment Variable

```
AthenaService.__init__():
  self.results_bucket = os.getenv("ATHENA_RESULTS_BUCKET")
  if not self.results_bucket:
    raise ConfigError("ATHENA_RESULTS_BUCKET environment variable not set")

Exception Handler:
  @app.exception_handler(VexError)
  → status_code = 500 (from ConfigError init)
  → return JSONResponse(status_code=500, content={
      "error": "ConfigError",
      "detail": "ATHENA_RESULTS_BUCKET environment variable not set"
    })

Response:
  HTTP/1.1 500 Internal Server Error
  {
    "error": "ConfigError",
    "detail": "ATHENA_RESULTS_BUCKET environment variable not set"
  }
```

---

## Testing Strategy

### Unit Tests
- `test_utils/test_validation.py` — Test validators with good/bad inputs
- `test_services/test_athena.py` — Mock boto3/awswrangler, test query building
- `test_utils/test_transform.py` — Test zone_to_feature, CFR calc

### Integration Tests
- Mock Athena → return fixture data → verify response model matches
- Test cache hit/miss cycles
- Test error handling paths

### Fixtures Mode
- `VEX_LOCAL_FIXTURES=1` → loads from `data/fixtures/*.json`
- No AWS dependencies needed
- Full API testing without costs

---

## Production Considerations

1. **CORS** — Currently allows all origins; restrict to frontend domain
2. **Rate Limiting** — Add via FastAPI middleware or API Gateway
3. **Authentication** — Add API key / OAuth2 if needed
4. **Logging** — Structured JSON logs for CloudWatch
5. **Monitoring** — CloudWatch alarms on error rates, latency
6. **Lambda Cold Start** — Consider provisioned concurrency
7. **Timeout** — Current 30s; may need adjustment based on query complexity

