import pathlib

import json
from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    BundlingOptions,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_apigateway as apigw,
    aws_cognito as cognito)
from constructs import Construct
from cdk_nag import NagSuppressions, NagPackSuppression
import os.path

class ProjectDatabase(Construct):
    def __init__(
        self,
        scope: Construct,
        id_: str
    ):
        super().__init__(scope, id_)

        log_level = "INFO"
        
        #todo
