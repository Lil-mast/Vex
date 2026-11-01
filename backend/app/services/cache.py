"""Caching service for Vex API results."""

import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any, List
import boto3
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheService:
    """Handles in-memory and S3 caching of query results."""

    def __init__(self):
        """Initialize cache service."""
        self.in_memory_cache: Dict[str, Any] = {}
        self.cache_ttl_seconds = 300  # 5 minutes
        self.s3_client = boto3.client(
            "s3",
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        self.cache_bucket = os.getenv("LAKE_BUCKET")

    def _generate_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate a cache key from endpoint and parameters."""
        # Sort params for consistent keys
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        hash_val = hashlib.sha256(sorted_params.encode()).hexdigest()
        return f"{endpoint}:{hash_val}"

    def _get_s3_cache_key(self, cache_key: str) -> str:
        """Convert cache key to S3 path."""
        return f"cache/{cache_key}.json"

    def get(self, endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        Get cached result from in-memory or S3.
        
        Args:
            endpoint: API endpoint name (e.g., "zones")
            params: Query parameters dict
            
        Returns:
            Cached result or None if not found/expired
        """
        cache_key = self._generate_cache_key(endpoint, params)

        # Try in-memory cache first
        if cache_key in self.in_memory_cache:
            cached_data = self.in_memory_cache[cache_key]
            if cached_data["expires_at"] > datetime.utcnow():
                logger.debug(f"Cache hit (memory): {cache_key}")
                return cached_data["result"]
            else:
                # Expired, remove
                del self.in_memory_cache[cache_key]

        # Try S3 cache
        if self.cache_bucket:
            try:
                s3_key = self._get_s3_cache_key(cache_key)
                response = self.s3_client.get_object(
                    Bucket=self.cache_bucket,
                    Key=s3_key
                )
                cached_data = json.loads(response["Body"].read().decode())

                if cached_data["expires_at"] > datetime.utcnow().isoformat():
                    logger.debug(f"Cache hit (S3): {cache_key}")
                    # Restore to in-memory cache
                    self.in_memory_cache[cache_key] = {
                        "result": cached_data["result"],
                        "expires_at": datetime.fromisoformat(cached_data["expires_at"])
                    }
                    return cached_data["result"]
            except self.s3_client.exceptions.NoSuchKey:
                pass
            except Exception as e:
                logger.warning(f"S3 cache read failed: {str(e)}")

        return None

    def set(self, endpoint: str, params: Dict[str, Any], result: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Cache a result in memory and S3.
        
        Args:
            endpoint: API endpoint name
            params: Query parameters dict
            result: Result to cache
            ttl_seconds: Time-to-live (uses default if None)
        """
        if ttl_seconds is None:
            ttl_seconds = self.cache_ttl_seconds

        cache_key = self._generate_cache_key(endpoint, params)
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

        # In-memory cache
        self.in_memory_cache[cache_key] = {
            "result": result,
            "expires_at": expires_at
        }

        # S3 cache
        if self.cache_bucket:
            try:
                s3_key = self._get_s3_cache_key(cache_key)
                cache_data = {
                    "result": result,
                    "expires_at": expires_at.isoformat(),
                    "cached_at": datetime.utcnow().isoformat()
                }
                self.s3_client.put_object(
                    Bucket=self.cache_bucket,
                    Key=s3_key,
                    Body=json.dumps(cache_data),
                    ContentType="application/json"
                )
                logger.debug(f"Cached result to S3: {cache_key}")
            except Exception as e:
                logger.warning(f"S3 cache write failed: {str(e)}")

    def clear(self, endpoint: Optional[str] = None) -> None:
        """Clear cache (all or specific endpoint)."""
        if endpoint is None:
            self.in_memory_cache.clear()
            logger.info("Cleared all in-memory cache")
        else:
            keys_to_remove = [k for k in self.in_memory_cache.keys() if k.startswith(endpoint)]
            for k in keys_to_remove:
                del self.in_memory_cache[k]
            logger.info(f"Cleared cache for endpoint: {endpoint}")
