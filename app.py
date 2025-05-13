#!/usr/bin/env python3
import os

from aws_cdk import App, Aspects, Environment
from stacks import AppLayerStack, TanStackRouterStack, SharedResourcesStack
from cdk_nag import AwsSolutionsChecks

app = App()

description = '''
This is a starter template for deploying a TanStack router app using Amazon CloudFront and Amazon S3, and
a serverless app layer stack which leverages API Gateway, Lambda (Python, Flask), and DynamoDB.
The repo contains a shared stack which initially contains just a cognito user pool which will be used by
both the App stack and the TanStack web app.
'''

app_layer_stack = AppLayerStack(app, "SampleAppLayerStack",
    description=description
)

tan_stack_router_app_stack = TanStackRouterStack(app, "SampleTanStackRouterAppStack",
    description=description
)

tan_stack_router_app_stack = SharedResourcesStack(app, "SampleSharedResourcesStack",
    description=description
)

Aspects.of(app).add(AwsSolutionsChecks())

app.synth()
