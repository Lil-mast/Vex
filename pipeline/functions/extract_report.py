"""Pipeline boundary for report extraction; preserve the source for review."""
import json
import os

import boto3

s3 = boto3.client("s3")


def handler(event, context):
    # Bedrock PDF extraction needs an agreed prompt/schema and configured model.
    # Do not produce clinical numbers until those are supplied and validated.
    manifest = event.get("Payload", event)
    key = manifest.get("s3_raw_key")
    if not key:
        raise ValueError("Expected s3_raw_key from FetchReports")
    review = {**manifest, "status": "needs_review", "reason": "Extraction schema and Bedrock model configuration are pending"}
    review_key = f"review/{manifest.get('report_id', 'unknown')}.json"
    s3.put_object(Bucket=os.environ["RAW_BUCKET"], Key=review_key, Body=json.dumps(review).encode(), ContentType="application/json")
    return {**manifest, "status": "needs_review", "review_key": review_key}
