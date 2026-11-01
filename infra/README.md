# AWS infrastructure

Python AWS CDK v2 application for Vex. The initial deployment provisions private encrypted data buckets, Glue/Athena, a scheduled Step Functions ingestion workflow, an API Lambda behind HTTP API, and a private static web bucket behind CloudFront. A Location Service key is created with the configured allowed origins.

## Prerequisites

- Python 3.12 and `uv`
- Node.js and the AWS CDK CLI (`npm install -g aws-cdk`)
- AWS credentials with deployment permissions
- CDK bootstrap in the target account and region

```sh
cd infra
uv sync
cdk synth
cdk bootstrap aws://ACCOUNT_ID/REGION
cdk deploy --all
```

Set `CDK_DEFAULT_ACCOUNT` and `CDK_DEFAULT_REGION`, or use the normal AWS CLI profile resolution. `VEX_ENV` defaults to `dev`; `VEX_ALLOWED_ORIGINS` accepts a comma-separated list for the Location Service key. Review IAM and the generated templates before deploying into a production account.

Pipeline source URLs are configured in the `VEX_REPORT_SOURCES` Lambda environment variable as a JSON array of `{ "url": "https://...", "source": "..." }` objects. The fetch step stores new PDFs and a content-hash manifest in the raw bucket. Later stages deliberately record an explicit `needs_review` result until the report extraction, validation, and Iceberg table contracts are implemented.

Destroying stacks deletes data buckets only when empty. Keep production data and state protected with backups and an explicit retention policy.
