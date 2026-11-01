from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_athena as athena
from aws_cdk import aws_glue as glue
from aws_cdk import aws_s3 as s3
from constructs import Construct


class DataStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, prefix: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        retain = RemovalPolicy.RETAIN
        account_suffix = self.account
        self.raw_bucket = self._bucket("Raw", f"{prefix}-raw-{account_suffix}", retain)
        self.lake_bucket = self._bucket("Lake", f"{prefix}-lake-{account_suffix}", retain)
        self.athena_results_bucket = self._bucket("AthenaResults", f"{prefix}-athena-results-{account_suffix}", retain)
        self.database = glue.CfnDatabase(
            self, "GlueDatabase", catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(name=f"{prefix.replace('-', '_')}_catalog"),
        )
        self.workgroup = athena.CfnWorkGroup(
            self, "AthenaWorkgroup", name=prefix,
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                enforce_work_group_configuration=True,
                publish_cloud_watch_metrics_enabled=True,
                bytes_scanned_cutoff_per_query=10_000_000_000,
                engine_version=athena.CfnWorkGroup.EngineVersionProperty(
                    selected_engine_version="Athena engine version 3"
                ),
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{self.athena_results_bucket.bucket_name}/query-results/",
                    encryption_configuration=athena.CfnWorkGroup.EncryptionConfigurationProperty(
                        encryption_option="SSE_S3"
                    ),
                ),
            ),
        )
        CfnOutput(self, "RawBucketName", value=self.raw_bucket.bucket_name)
        CfnOutput(self, "LakeBucketName", value=self.lake_bucket.bucket_name)
        CfnOutput(self, "AthenaResultsBucketName", value=self.athena_results_bucket.bucket_name)
        CfnOutput(self, "GlueDatabaseName", value=self.database.ref)

    def _bucket(self, name: str, bucket_name: str, removal: RemovalPolicy) -> s3.Bucket:
        return s3.Bucket(
            self, name, bucket_name=bucket_name,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True, versioned=True,
            removal_policy=removal, auto_delete_objects=False,
        )
