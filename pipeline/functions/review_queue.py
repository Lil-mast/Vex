"""Persist pipeline review outcomes until validation and Iceberg schemas exist."""
import json
import os

import boto3

s3 = boto3.client("s3")


def handler(event, context):
    report = event.get("Payload", event)
    report.setdefault("status", "needs_review")
    report.setdefault("reason", "Validation and Iceberg loading are not configured")
    key = report.get("review_key") or f"review/{report.get('report_id', 'unknown')}.json"
    s3.put_object(Bucket=os.environ["RAW_BUCKET"], Key=key, Body=json.dumps(report).encode(), ContentType="application/json")
    return {"report_id": report.get("report_id"), "status": report["status"], "review_key": key}
