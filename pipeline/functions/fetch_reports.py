"""Download configured public reports and save only unseen content hashes."""
import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

s3 = boto3.client("s3")


def handler(event, context):
    bucket = os.environ["RAW_BUCKET"]
    sources = json.loads(os.environ.get("VEX_REPORT_SOURCES", "[]"))
    reports = []
    for source in sources:
        url = source["url"]
        request = urllib.request.Request(url, headers={"User-Agent": "VexOutbreakAtlas/1.0 (public health data; contact: ops@example.org)"})
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read()
            content_type = response.headers.get("Content-Type", "")
        if not content.startswith(b"%PDF-"):
            raise ValueError(f"Configured source did not return a PDF: {url}")
        digest = hashlib.sha256(content).hexdigest()
        key = f"{source.get('source', 'unknown')}/{digest}.pdf"
        try:
            s3.head_object(Bucket=bucket, Key=key)
            continue
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") not in {"404", "NoSuchKey", "NotFound"}:
                raise
        s3.put_object(Bucket=bucket, Key=key, Body=content, ContentType="application/pdf")
        manifest = {
            "report_id": digest, "source": source.get("source", "unknown"),
            "url": url, "s3_raw_key": key, "sha256": digest,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "content_type": content_type,
        }
        manifest_key = f"manifests/{digest}.json"
        s3.put_object(Bucket=bucket, Key=manifest_key, Body=json.dumps(manifest).encode(), ContentType="application/json")
        reports.append(manifest)
    return {"new_reports": reports, "fetched_count": len(reports)}
