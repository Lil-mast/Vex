from aws_cdk import CfnOutput, Duration, Stack
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_integrations as integrations
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from constructs import Construct


class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, prefix: str, data, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.function = lambda_.DockerImageFunction(
            self, "ApiFunction", function_name=f"{prefix}-api",
            code=lambda_.DockerImageCode.from_image_asset("../backend", cmd=["app.main.handler"]), memory_size=512,
            timeout=Duration.seconds(30), environment={
                "AWS_REGION": self.region,
                "RAW_BUCKET": data.raw_bucket.bucket_name,
                "LAKE_BUCKET": data.lake_bucket.bucket_name,
                "ATHENA_RESULTS_BUCKET": data.athena_results_bucket.bucket_name,
                "ATHENA_WORKGROUP": data.workgroup.name,
                "GLUE_DATABASE": data.database.ref,
            },
        )
        self.function.add_to_role_policy(iam.PolicyStatement(
            actions=["athena:StartQueryExecution", "athena:GetQueryExecution", "athena:GetQueryResults", "athena:StopQueryExecution"],
            resources=["*"],
        ))
        self.function.add_to_role_policy(iam.PolicyStatement(
            actions=["glue:GetDatabase", "glue:GetTable", "glue:GetPartitions"], resources=["*"],
        ))
        data.lake_bucket.grant_read_write(self.function, "cache/*")
        data.athena_results_bucket.grant_read_write(self.function, "query-results/*")
        self.http_api = apigwv2.HttpApi(
            self, "HttpApi", api_name=f"{prefix}-api",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_headers=["content-type", "authorization"],
                allow_methods=[apigwv2.CorsHttpMethod.GET, apigwv2.CorsHttpMethod.OPTIONS],
                allow_origins=["*"], max_age=Duration.hours(1),
            ),
        )
        self.http_api.add_routes(
            path="/{proxy+}", methods=[apigwv2.HttpMethod.ANY],
            integration=integrations.HttpLambdaIntegration("ApiIntegration", self.function),
        )
        CfnOutput(self, "ApiEndpoint", value=self.http_api.api_endpoint)
        self.http_api.add_routes(
            path="/", methods=[apigwv2.HttpMethod.ANY],
            integration=integrations.HttpLambdaIntegration("ApiRootIntegration", self.function),
        )
