"""AWS CDK application for the stac-fastapi-geoparquet Stack

Generates a Lambda function with an API Gateway trigger and an S3 bucket.
"""

import os
from typing import Any

from aws_cdk import (
    App,
    CfnOutput,
    Duration,
    Stack,
    Tags,
)
from aws_cdk.aws_apigatewayv2 import (
    DomainName,
    HttpApi,
    HttpStage,
    MappingValue,
    ParameterMapping,
    ThrottleSettings,
)
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from aws_cdk.aws_certificatemanager import Certificate
from aws_cdk.aws_iam import AnyPrincipal, Effect, PolicyStatement
from aws_cdk.aws_lambda import Code, Function, Handler, Runtime
from aws_cdk.aws_s3 import Bucket
from constructs import Construct

from config import Config


class StacFastApiGeoparquetStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Config,
        runtime: Runtime = Runtime.PYTHON_3_13,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        for key, value in config.tags.items():
            Tags.of(self).add(key, value)

        bucket = Bucket.from_bucket_name(
            self,
            id="bucket",
            bucket_name=config.bucket_name,
        )
        bucket.add_to_resource_policy(
            PolicyStatement(
                actions=["s3:GetObject"],
                resources=[bucket.arn_for_objects("*")],
                principals=[AnyPrincipal()],
                effect=Effect.ALLOW,
            )
        )

        api_lambda = Function(
            scope=self,
            id="lambda",
            runtime=Runtime.FROM_IMAGE,
            handler=Handler.FROM_IMAGE,
            memory_size=config.memory,
            timeout=Duration.seconds(config.timeout),
            code=Code.from_asset_image(
                directory=os.path.abspath("."),
                file="lambda/Dockerfile",
            ),
            environment={
                "STAC_FASTAPI_COLLECTIONS_HREF": f"s3://{bucket.bucket_name}/{config.collections_key}",
                "HOME": "/tmp",  # for duckdb's home_directory
            },
        )

        bucket.grant_read(api_lambda)

        self.domain_name = DomainName(
            self,
            "api-domain-name",
            domain_name=config.domain_name,
            certificate=Certificate.from_certificate_arn(
                self, "api-cdn-certificate", certificate_arn=config.certificate_arn
            ),
        )
        api = HttpApi(
            scope=self,
            id="api",
            default_integration=HttpLambdaIntegration(
                "api-integration",
                handler=api_lambda,
                parameter_mapping=ParameterMapping().overwrite_header(
                    "host", MappingValue.custom(self.domain_name.name)
                ),
            ),
            create_default_stage=False,  # Important: disable default stage creation
        )

        stage = HttpStage(
            self,
            "api-stage",
            http_api=api,
            auto_deploy=True,
            stage_name="$default",
            throttle=ThrottleSettings(
                rate_limit=config.rate_limit,
                burst_limit=config.rate_limit * 2,
            )
            if config.rate_limit
            else None,
        )

        assert stage.url
        CfnOutput(self, "ApiURL", value=stage.url)


app = App()
config = Config()
StacFastApiGeoparquetStack(
    app,
    config.stack_name,
    config=config,
)
app.synth()
