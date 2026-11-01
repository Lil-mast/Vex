import os

from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_location as location
from constructs import Construct


class LocationStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, prefix: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        allowed_origins = [item.strip() for item in os.getenv("VEX_ALLOWED_ORIGINS", "http://localhost:3000").split(",") if item.strip()]
        key = location.CfnAPIKey(
            self, "MapApiKey", key_name=f"{prefix}-map-key",
            restrictions=location.CfnAPIKey.ApiKeyRestrictionsProperty(
                allow_origins=allowed_origins,
                allow_actions=["geo:GetMapTile", "geo:GetMapStyleDescriptor", "geo:GetMapSprites", "geo:GetMapGlyphs"],
            ),
        )
        CfnOutput(self, "LocationApiKey", value=key.attr_key, description="Restricted browser map key; review allowed origins before production use")
