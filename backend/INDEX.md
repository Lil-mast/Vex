# Backend Documentation Files

All documentation is in the backend/ root directory.

## Read These First (In Order)

1. DESIGN.md - High-level architecture overview
2. ARCHITECTURE_LAYERS.md - Detailed layer diagrams and data flows
3. FILE_MANIFEST.md - File listing and quick reference
4. BACKEND_BUILD_STATUS.md - Progress tracker

## Files Created in Piece 2

- app/main.py - FastAPI app setup
- app/exceptions.py - Custom error types
- app/models.py - Pydantic response schemas (15+)
- app/services/athena.py - Athena query service
- app/services/cache.py - In-memory + S3 caching
- app/utils/validation.py - Query param validators
- app/utils/transform.py - Result transformation helpers

## Next Steps (Piece 3)

Create routers that wire the services:
- app/routers/zones.py
- app/routers/countries.py
- app/routers/events.py
- app/routers/snapshots.py
- app/routers/quality.py

All files checked for syntax errors and ready to use.
