#!/usr/bin/env python3
import os

from aws_cdk import App, Aspects, Environment
from app_components.project_svc_backend.component import ProjectBackend
from app_components.frontend.component import FrontEndHosting
from app_components.shared.component import SharedServices
from cdk_nag import AwsSolutionsChecks

app = App()

description = '''
This is a starter template for deploying a TanStack router app using Amazon CloudFront and Amazon S3, and
a serverless app layer stack which leverages API Gateway, Lambda (Python, Flask), and DynamoDB.
The repo contains a shared stack which initially contains just a cognito user pool which will be used by
both the App stack and the TanStack web app.
'''

ss = SharedServices(
    app,
    "SharedServices" + "Sandbox",
    description=description,
)

pb = ProjectBackend(
    app,
    "ProjectSvcBackend" + "Sandbox",
    description=description,
    dynamodb_table_name="Projects",
)

feh = FrontEndHosting(
    app,
    "FrontEndHosting" + "Sandbox",
    description=description,
)

feh.add_dependency(ss)

Aspects.of(app).add(AwsSolutionsChecks())

app.synth()
