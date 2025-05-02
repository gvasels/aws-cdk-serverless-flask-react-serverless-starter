#!/usr/bin/env python3
import os

from aws_cdk import App, Aspects, Environment
from stacks import AppLayerStack, ReactRouterAppStack
from cdk_nag import AwsSolutionsChecks

app = App()

description = '''
This is a starter template for deploying a react router app using Amazon CloudFront and Amazon S3,
as well as a serverless app layer stack which leverages API Gateway, Lambda (Python, Flask), and DynamoDB.
'''

app_layer_stack = AppLayerStack(app, "SampleAppLayerStack",
    description=description
)

react_router_app_stack = ReactRouterAppStack(app, "SampleReactRouterAppStack",
    description=description
)

Aspects.of(app).add(AwsSolutionsChecks())

app.synth()
