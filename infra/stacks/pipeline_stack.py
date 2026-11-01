import os

from aws_cdk import CfnOutput, Duration, Stack
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_sns as sns
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as tasks
from constructs import Construct


class PipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, prefix: str, data, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        code = lambda_.Code.from_asset("../pipeline/functions")
        common = dict(runtime=lambda_.Runtime.PYTHON_3_12, code=code, timeout=Duration.minutes(5), memory_size=512)
        self.fetch = lambda_.Function(
            self, "FetchReports", function_name=f"{prefix}-fetch-reports", handler="fetch_reports.handler",
            **common, environment={
                "RAW_BUCKET": data.raw_bucket.bucket_name,
                "VEX_REPORT_SOURCES": os.getenv("VEX_REPORT_SOURCES", "[]"),
            },
        )
        data.raw_bucket.grant_read_write(self.fetch)
        self.extract = lambda_.Function(
            self, "ExtractReport", function_name=f"{prefix}-extract-report", handler="extract_report.handler",
            **common, environment={"RAW_BUCKET": data.raw_bucket.bucket_name},
        )
        data.raw_bucket.grant_read_write(self.extract)
        self.review = lambda_.Function(
            self, "QueueReview", function_name=f"{prefix}-review-queue", handler="review_queue.handler",
            **common, environment={"RAW_BUCKET": data.raw_bucket.bucket_name},
        )
        data.raw_bucket.grant_read_write(self.review)

        fetch_task = tasks.LambdaInvoke(self, "Fetch", lambda_function=self.fetch, output_path="$.Payload")
        map_task = sfn.Map(self, "ProcessNewReports", items_path="$.new_reports", max_concurrency=3, result_path="$.report_results")
        map_task.item_processor(sfn.Chain.start(
            tasks.LambdaInvoke(self, "Extract", lambda_function=self.extract, output_path="$.Payload")
            .add_catch(sfn.Pass(self, "ExtractionNeedsReview", result=sfn.Result.from_object({"status": "needs_review"})), result_path="$.error")
        ).next(tasks.LambdaInvoke(self, "QueueReview", lambda_function=self.review, output_path="$.Payload")))
        definition = fetch_task.next(map_task)
        self.state_machine = sfn.StateMachine(
            self, "IngestStateMachine", state_machine_name=f"{prefix}-ingest",
            definition_body=sfn.DefinitionBody.from_chainable(definition), timeout=Duration.hours(2),
            logs=sfn.LogOptions(destination=logs.LogGroup(self, "PipelineLogs", retention=logs.RetentionDays.ONE_MONTH), level=sfn.LogLevel.ALL),
        )
        failures = sns.Topic(self, "PipelineFailures", topic_name=f"{prefix}-pipeline-failures")
        failures.grant_publish(iam.ServicePrincipal("events.amazonaws.com"))
        events.Rule(
            self, "DailySchedule", schedule=events.Schedule.cron(minute="0", hour="6"),
            targets=[targets.SfnStateMachine(self.state_machine)],
        )
        CfnOutput(self, "IngestStateMachineArn", value=self.state_machine.state_machine_arn)
        CfnOutput(self, "PipelineFailureTopicArn", value=failures.topic_arn)
        events.Rule(
            self, "ExecutionFailureAlarm", event_pattern=events.EventPattern(
                source=["aws.states"], detail_type=["Step Functions Execution Status Change"],
                detail={"status": ["FAILED", "TIMED_OUT", "ABORTED"], "stateMachineArn": [self.state_machine.state_machine_arn]},
            ), targets=[targets.SnsTopic(failures)],
        )
