import os

import aws_cdk as cdk

from stacks.api_stack import ApiStack
from stacks.data_stack import DataStack
from stacks.location_stack import LocationStack
from stacks.pipeline_stack import PipelineStack
from stacks.web_stack import WebStack

app = cdk.App()
env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION", "us-east-1"),
)
stage = app.node.try_get_context("stage") or os.getenv("VEX_ENV", "dev")
prefix = f"vex-{stage}"

data = DataStack(app, "VexData", env=env, prefix=prefix)
pipeline = PipelineStack(app, "VexPipeline", env=env, prefix=prefix, data=data)
api = ApiStack(app, "VexApi", env=env, prefix=prefix, data=data)
web = WebStack(app, "VexWeb", env=env, prefix=prefix, api=api)
location = LocationStack(app, "VexLocation", env=env, prefix=prefix)

pipeline.add_dependency(data)
api.add_dependency(data)
web.add_dependency(api)

app.synth()
