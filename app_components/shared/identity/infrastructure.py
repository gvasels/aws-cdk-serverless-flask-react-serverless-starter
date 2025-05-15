import pathlib

import json
from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_iam as iam,
    aws_cognito as cognito,
    RemovalPolicy)
from constructs import Construct
from cdk_nag import NagSuppressions, NagPackSuppression
import os.path

class Identity(Construct):
    def __init__(
        self,
        scope: Construct,
        id_: str
    ):
        super().__init__(scope, id_)

        log_level = "INFO"
        
        #create a cognito user pool
        user_pool = cognito.UserPool(
            self,
            'serverless-starter-pool',
            user_pool_name='serverless-starter-pool',
            self_sign_up_enabled=True,
            # user_verification=cognito.UserVerificationConfig(
            #     email_subject="Verify your email for our awesome app!",
            #     email_body="Thanks for signing up to our awesome app! Your verification code is {####}",
            #     email_style=cognito.VerificationEmailStyle.CODE
            # ),
            sign_in_aliases=cognito.SignInAliases(username=True, email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
                temp_password_validity=Duration.days(7)
            ),
            removal_policy=RemovalPolicy.DESTROY
        )
        
        self.user_pool = user_pool

        # Add suppression for the imported user pool
        NagSuppressions.add_resource_suppressions(
            user_pool,
            suppressions=[
                NagPackSuppression(
                    id="AwsSolutions-COG3",
                    reason="This is a sample application which does not require Cognito's advanced features."
                ),
                NagPackSuppression(
                    id="AwsSolutions-COG2",
                    reason="MFA is not required for this application."
                )
            ]
        )
