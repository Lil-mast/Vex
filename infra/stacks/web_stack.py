from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_s3 as s3
from constructs import Construct


class WebStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, prefix: str, api, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.bucket = s3.Bucket(
            self, "WebBucket", bucket_name=f"{prefix}-web-{self.account}",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED, enforce_ssl=True,
            removal_policy=RemovalPolicy.RETAIN,
        )
        self.distribution = cloudfront.Distribution(
            self, "Distribution", default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(self.bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                compress=True,
            ),
            additional_behaviors={
                "api/*": cloudfront.BehaviorOptions(
                    origin=origins.HttpOrigin(api.http_api.api_id + ".execute-api." + self.region + ".amazonaws.com"),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                    compress=True,
                ),
            },
            error_responses=[
                cloudfront.ErrorResponse(http_status=403, response_http_status=200, response_page_path="/index.html", ttl=Duration.minutes(1)),
                cloudfront.ErrorResponse(http_status=404, response_http_status=200, response_page_path="/index.html", ttl=Duration.minutes(1)),
            ],
        )
        CfnOutput(self, "DistributionDomainName", value=self.distribution.domain_name)
        CfnOutput(self, "WebBucketName", value=self.bucket.bucket_name)
