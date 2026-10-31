# Pipeline

AWS Lambda functions for the data extraction pipeline.

- fetch_reports/ — Download PDFs from sources
- extract_report/ — Bedrock/Textract extraction
- validate_load/ — Validation rules and Iceberg MERGE
- publish_snapshots/ — Precompute GeoJSON snapshots
- common/ — Shared schemas and utilities
