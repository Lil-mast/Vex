# AWS Setup Guide for Vex - Quick Reference

See README.md section 4 for AWS services overview.

## Quick Setup Steps

1. Create S3 buckets: vex-raw-{account-id}, vex-lake-{account-id}, vex-athena-{account-id}, vex-web-{account-id}
2. Create Glue database: vex
3. Create Athena workgroup: vex (engine v3, result location in vex-athena bucket, scan limit 100GB)
4. Confirm Bedrock Claude 3 model access in console
5. Create Location Service API key, restrict to localhost:3000 and your CloudFront domain
6. Run SQL CREATE TABLE statements in Athena (see ARCHITECTURE.md section 3)
7. Fill in backend/.env and web/.env.local with your values
8. Download boundary GeoJSON files to data/boundaries/

See README.md section 4 for detailed service descriptions and region selection.
