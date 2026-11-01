"""Athena query service for Vex API."""

import os
import logging
from typing import Optional, List, Dict, Any
import boto3
import awswrangler as wr
from botocore.exceptions import ClientError

from app.exceptions import ConfigError, AthenaError, AthenaTimeoutError

logger = logging.getLogger(__name__)


class AthenaService:
    """Handles Athena queries for zone, country, and event data."""

    def __init__(self):
        """Initialize Athena service with environment config."""
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.database = os.getenv("GLUE_DATABASE", "vex")
        self.workgroup = os.getenv("ATHENA_WORKGROUP", "vex")
        self.results_bucket = os.getenv("ATHENA_RESULTS_BUCKET")

        if not self.results_bucket:
            raise ConfigError("ATHENA_RESULTS_BUCKET environment variable not set")

        self.athena_client = boto3.client("athena", region_name=self.region)
        self.s3_client = boto3.client("s3", region_name=self.region)

    def execute_query(
        self,
        query: str,
        timeout_seconds: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Execute a parameterized SQL query via Athena.
        
        Args:
            query: SQL query string (must be safe, validated by caller)
            timeout_seconds: Query timeout in seconds
            
        Returns:
            List of result rows as dicts
            
        Raises:
            AthenaError: Query execution failed
            AthenaTimeoutError: Query exceeded timeout
        """
        try:
            logger.info(f"Executing Athena query (timeout {timeout_seconds}s)")
            
            # Use awswrangler for simplified query execution
            df = wr.athena.read_sql_query(
                sql=query,
                database=self.database,
                s3_output=f"s3://{self.results_bucket}/",
                workgroup=self.workgroup,
                boto3_session=boto3.Session(region_name=self.region),
                max_cache_seconds=0,  # No caching at query level (handled separately)
            )
            
            # Convert DataFrame to list of dicts
            results = df.to_dict(orient="records")
            logger.info(f"Query returned {len(results)} rows")
            return results

        except TimeoutError:
            logger.error("Athena query timed out")
            raise AthenaTimeoutError(f"Query timed out after {timeout_seconds}s")
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]
            logger.error(f"Athena error {error_code}: {error_msg}")
            raise AthenaError(f"Athena query failed: {error_msg}")
        except Exception as e:
            logger.error(f"Unexpected error executing query: {str(e)}", exc_info=True)
            raise AthenaError(f"Query execution failed: {str(e)}")

    def get_latest_date(self) -> Optional[str]:
        """Get the latest data_as_of date from zone_report table."""
        query = """
        SELECT DISTINCT data_as_of
        FROM {database}.zone_report
        ORDER BY data_as_of DESC
        LIMIT 1
        """.format(database=self.database)
        
        try:
            results = self.execute_query(query)
            if results:
                return str(results[0].get("data_as_of"))
            return None
        except AthenaError:
            logger.warning("Failed to get latest date from Athena")
            return None

    def get_dates(self) -> List[Dict[str, Any]]:
        """Get all distinct data_as_of dates with report validation counts."""
        query = """
        SELECT
            data_as_of,
            COUNT(DISTINCT report_id) as reports_count,
            SUM(CASE WHEN validated = true THEN 1 ELSE 0 END) as validation_passed,
            SUM(CASE WHEN validated = false THEN 1 ELSE 0 END) as validation_failed
        FROM {database}.zone_report
        GROUP BY data_as_of
        ORDER BY data_as_of DESC
        """.format(database=self.database)
        
        results = self.execute_query(query)
        return results

    def get_zones_for_date(
        self,
        data_as_of: str,
        metric: str = "cases_cum",
        province: Optional[str] = None,
        active_21d: bool = False,
        snapshot_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get zone data for a specific date.
        
        Args:
            data_as_of: Date string (YYYY-MM-DD)
            metric: One of: cases_cum, cases_new_7d, deaths_cum, cfr
            province: Optional province filter
            active_21d: Filter to zones with cases in last 21 days
            snapshot_id: Optional Iceberg snapshot ID for time travel
            
        Returns:
            List of zone records with all metrics
        """
        # Build query with optional filters
        where_clauses = [f"z.data_as_of = '{data_as_of}'"]

        if province:
            where_clauses.append(f"z.province = '{province}'")

        if active_21d:
            where_clauses.append("z.cases_new_7d > 0")

        where_sql = " AND ".join(where_clauses)

        # Snapshot handling (if snapshot_id provided, use FOR VERSION AS OF)
        snapshot_clause = ""
        if snapshot_id:
            snapshot_clause = f" FOR VERSION AS OF {snapshot_id}"

        query = f"""
        SELECT
            z.zone_key,
            z.health_zone,
            z.province,
            z.country,
            z.cases_cum,
            z.deaths_cum,
            z.cases_new_7d,
            z.deaths_new_7d,
            CAST(z.deaths_cum AS FLOAT) / NULLIF(z.cases_cum, 0) as cfr,
            z.validated,
            z.is_unassigned,
            z.extraction_confidence
        FROM {self.database}.zone_report{snapshot_clause} z
        WHERE {where_sql}
        ORDER BY z.health_zone
        """

        return self.execute_query(query)

    def get_zone_timeseries(self, zone_key: str) -> List[Dict[str, Any]]:
        """Get historical data for a single zone."""
        query = f"""
        SELECT
            data_as_of,
            cases_cum,
            deaths_cum,
            cases_new_7d,
            deaths_new_7d
        FROM {self.database}.zone_report
        WHERE zone_key = '{zone_key}'
        ORDER BY data_as_of ASC
        """

        return self.execute_query(query)

    def get_countries(self, data_as_of: str) -> List[Dict[str, Any]]:
        """Get country-level totals for a date."""
        query = f"""
        SELECT
            country,
            cases_cum,
            deaths_cum
        FROM {self.database}.country_report
        WHERE data_as_of = '{data_as_of}'
        ORDER BY cases_cum DESC
        """

        return self.execute_query(query)

    def get_kenya_counties(self, data_as_of: str) -> List[Dict[str, Any]]:
        """Get Kenya county-level data."""
        query = f"""
        SELECT
            zone_key,
            health_zone as county,
            cases_cum
        FROM {self.database}.zone_report
        WHERE country = 'Kenya' AND data_as_of = '{data_as_of}'
        ORDER BY cases_cum DESC
        """

        return self.execute_query(query)

    def get_events(
        self,
        data_as_of: str,
        country: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get curated events up to a date."""
        where_clauses = [f"event_date <= '{data_as_of}'"]

        if country:
            where_clauses.append(f"country = '{country}'")

        where_sql = " AND ".join(where_clauses)

        query = f"""
        SELECT
            event_id,
            event_date,
            country,
            admin1,
            event_type,
            description,
            source_url
        FROM {self.database}.events
        WHERE {where_sql}
        ORDER BY event_date DESC
        """

        return self.execute_query(query)

    def get_quality_metrics(self, data_as_of: str) -> Dict[str, Any]:
        """Get data quality metrics (unassigned cases, validation status)."""
        # Total unassigned cases
        unassigned_query = f"""
        SELECT SUM(cases_cum) as unassigned_cases
        FROM {self.database}.zone_report
        WHERE data_as_of = '{data_as_of}' AND is_unassigned = true
        """

        # Total cases
        total_query = f"""
        SELECT SUM(cases_cum) as total_cases
        FROM {self.database}.zone_report
        WHERE data_as_of = '{data_as_of}'
        """

        # Validation status per report
        validation_query = f"""
        SELECT
            report_id,
            SUM(CASE WHEN validated = true THEN 1 ELSE 0 END) as rules_passed,
            SUM(CASE WHEN validated = false THEN 1 ELSE 0 END) as rules_failed,
            AVG(extraction_confidence) as confidence
        FROM {self.database}.zone_report
        WHERE data_as_of = '{data_as_of}'
        GROUP BY report_id
        """

        unassigned_results = self.execute_query(unassigned_query)
        total_results = self.execute_query(total_query)
        validation_results = self.execute_query(validation_query)

        unassigned_cases = unassigned_results[0].get("unassigned_cases", 0) or 0
        total_cases = total_results[0].get("total_cases", 1)  # Avoid div by zero
        unassigned_share = unassigned_cases / total_cases if total_cases > 0 else 0

        return {
            "unassigned_cases": unassigned_cases,
            "unassigned_share": unassigned_share,
            "reports": validation_results,
        }

    def get_snapshots(self) -> List[Dict[str, Any]]:
        """Get list of Iceberg snapshots."""
        query = f"""
        SELECT
            snapshot_id,
            committed_at,
            operation
        FROM {self.database}.zone_report$snapshots
        ORDER BY committed_at DESC
        """

        return self.execute_query(query)

    def get_diff(
        self,
        from_snapshot_id: int,
        to_snapshot_id: int,
        data_as_of: str
    ) -> List[Dict[str, Any]]:
        """Get rows that changed between two snapshots."""
        query = f"""
        SELECT DISTINCT
            from_tbl.zone_key,
            from_tbl.health_zone,
            from_tbl.province,
            from_tbl.data_as_of,
            from_tbl.cases_cum as old_cases_cum,
            to_tbl.cases_cum as new_cases_cum,
            from_tbl.deaths_cum as old_deaths_cum,
            to_tbl.deaths_cum as new_deaths_cum
        FROM {self.database}.zone_report FOR VERSION AS OF {from_snapshot_id} from_tbl
        FULL OUTER JOIN {self.database}.zone_report FOR VERSION AS OF {to_snapshot_id} to_tbl
            ON from_tbl.zone_key = to_tbl.zone_key
            AND from_tbl.data_as_of = to_tbl.data_as_of
        WHERE (from_tbl.cases_cum != to_tbl.cases_cum
            OR from_tbl.deaths_cum != to_tbl.deaths_cum
            OR from_tbl IS NULL
            OR to_tbl IS NULL)
        ORDER BY from_tbl.data_as_of, from_tbl.zone_key
        """

        return self.execute_query(query)
