"""Countries router — country-level and Kenya county data."""

from fastapi import APIRouter, Query
import logging

from app.services.athena import AthenaService
from app.services.cache import CacheService
from app.models import CountriesResponse, CountryDataPoint, KenyaCountiesResponse, KenyaCountyFeature, KenyaCountyProperties
from app.utils.validation import validate_date

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/countries", tags=["countries"])


@router.get("", response_model=CountriesResponse)
async def get_countries(
    data_as_of: str = Query(..., description="Date in YYYY-MM-DD format"),
):
    """
    Get country-level case and death totals.
    
    Includes DRC, Uganda, Kenya, Nigeria, Rwanda, South Sudan, and other affected countries.
    """
    # Validate input
    data_as_of = validate_date(data_as_of)
    
    # Check cache
    cache = CacheService()
    cache_key = {"data_as_of": data_as_of}
    cached_result = cache.get("countries", cache_key)
    if cached_result is not None:
        logger.debug(f"Cache hit for countries: {data_as_of}")
        return cached_result
    
    # Query Athena
    athena = AthenaService()
    country_records = athena.get_countries(data_as_of)
    
    # Transform to CountryDataPoint
    countries = []
    for record in country_records:
        point = CountryDataPoint(
            country=record.get("country"),
            cases_cum=int(record.get("cases_cum", 0)),
            deaths_cum=int(record.get("deaths_cum", 0)),
        )
        countries.append(point)
    
    # Build response
    response = CountriesResponse(
        data_as_of=data_as_of,
        countries=countries
    )
    
    # Cache result
    cache.set("countries", cache_key, response, ttl_seconds=300)
    
    return response


@router.get("/kenya/counties", response_model=KenyaCountiesResponse)
async def get_kenya_counties(
    data_as_of: str = Query(..., description="Date in YYYY-MM-DD format"),
):
    """
    Get Kenya county-level case data.
    
    Returns GeoJSON FeatureCollection with county-level aggregates.
    Kenya data is kept at county level only (no facility or patient level).
    """
    # Validate input
    data_as_of = validate_date(data_as_of)
    
    # Check cache
    cache = CacheService()
    cache_key = {"data_as_of": data_as_of, "country": "Kenya"}
    cached_result = cache.get("kenya_counties", cache_key)
    if cached_result is not None:
        logger.debug(f"Cache hit for Kenya counties: {data_as_of}")
        return cached_result
    
    # Query Athena
    athena = AthenaService()
    county_records = athena.get_kenya_counties(data_as_of)
    
    # Transform to GeoJSON Features
    features = []
    for county in county_records:
        properties = KenyaCountyProperties(
            county=county.get("county"),
            cases_cum=int(county.get("cases_cum", 0)),
        )
        # TODO: In Piece 4, fetch boundary geometry from boundaries service
        geometry = {
            "type": "Point",
            "coordinates": [0, 0]
        }
        feature = KenyaCountyFeature(
            type="Feature",
            geometry=geometry,
            properties=properties
        )
        features.append(feature)
    
    # Build response
    response = KenyaCountiesResponse(
        type="FeatureCollection",
        features=features
    )
    
    # Cache result
    cache.set("kenya_counties", cache_key, response, ttl_seconds=300)
    
    return response
