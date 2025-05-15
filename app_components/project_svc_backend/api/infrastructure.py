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

dirname = os.path.dirname(__file__)

class ProjectAPI(Construct):
    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        dynamodb_table_name: str,
        region_name: str,
        account_id: str
    ):
        super().__init__(scope, id_)

        log_level = "INFO"
        
        api_svc_lambda_role = iam.Role(
            self,
            'ApiSvcLambdaRole',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com')
        )

        api_svc_lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    'logs:CreateLogGroup',
                    'logs:CreateLogStream',
                    'logs:PutLogEvents'
                ],
                resources=[':'.join([
                    'arn',
                    'aws',
                    'logs',
                    region_name,
                    account_id,
                    'log-group',
                    '/aws/lambda/api-svc-lambda-flask',
                    '*'
                ])]
            )
        )

        NagSuppressions.add_resource_suppressions(
            api_svc_lambda_role,
            apply_to_children=True,
            suppressions=[
                NagPackSuppression(
                    id='AwsSolutions-IAM5',
                    reason='Wildcards are scoped appropriately'
                )
            ]
        )
        
        self.api_svc_lambda = lambda_.Function(
            self,
            'api-svc-lambda-flask',
            description='flask compute to handle CRUD events related to generating prompts for feature extraction',
            function_name='api-svc-lambda-flask',
            runtime=lambda_.Runtime.PYTHON_3_13,
            code=lambda_.Code.from_asset(
                os.path.join(dirname, './runtime'),
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_13.bundling_image,
                    command=[
                        "bash", "-c",
                        # First copy all python files to output
                        "cp -r . /asset-output && " +
                        # Create a temp directory for package installation
                        "mkdir -p /tmp/packages && " +
                        # Install packages to temp directory
                        "pip install --target=/tmp/packages -r requirements.txt && " +
                        # Copy packages to asset output using cp instead of tar
                        "cp -r /tmp/packages/* /asset-output/ && " +
                        # Clean up pycache files if they exist
                        "find /asset-output -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true && " +
                        "find /asset-output -name '*.pyc' -type f -delete || true"
                    ]
                )    
            ),
            role=api_svc_lambda_role,
            handler='handler.main',
            timeout=Duration.seconds(30),
            environment={
                'LOG_LEVEL': log_level
            }
        )

        NagSuppressions.add_resource_suppressions(
            self.api_svc_lambda,
            apply_to_children=True,
            suppressions=[
                NagPackSuppression(
                    id='AwsSolutions-L1',
                    reason='runtime version selected based on dependency support'
                )
            ]
        )

        #create REST API
        self.app_layer_api = apigw.RestApi(
            self,
            'sample-app-layer-api',
            description='API serving as the entrypoint for services running in Lambda or optionally containers',
            deploy_options=apigw.StageOptions(
                stage_name='api',
                tracing_enabled=True
            )
        )

        #add method to root resource
        root_method = self.app_layer_api.root.add_method(
            'GET',
            apigw.LambdaIntegration(
                self.api_svc_lambda
            )
        )

        #add profiles resource to root resource
        profiles_resource = self.app_layer_api.root.add_resource('profiles')

        #add profile_id resource to profiles_resource
        profile_id_resource = profiles_resource.add_resource('{profile_id}')

        #GET /profiles
        get_profiles = profiles_resource.add_method(
            'GET',
            apigw.LambdaIntegration(
                self.api_svc_lambda
            )
        )

        #GET /profiles/{profile_id}
        get_profile_id = profile_id_resource.add_method(
            'GET',
            apigw.LambdaIntegration(
                self.api_svc_lambda
            )
        )

        NagSuppressions.add_resource_suppressions(
            self.app_layer_api,
            apply_to_children=True,
            suppressions=[
                NagPackSuppression(
                    id='AwsSolutions-APIG2',
                    reason='Request Validation not set up'
                )
            ]
        )

        NagSuppressions.add_resource_suppressions(
            self.app_layer_api,
            apply_to_children=True,
            suppressions=[
                NagPackSuppression(
                    id='AwsSolutions-APIG2',
                    reason='Request Validation not set up'
                )
            ]
        )

        NagSuppressions.add_resource_suppressions(
            self.app_layer_api.deployment_stage,
            apply_to_children=True,
            suppressions=[
                NagPackSuppression(
                    id="AwsSolutions-APIG1",
                    reason="Access logging is not required for this development API"
                ),
                NagPackSuppression(
                    id="AwsSolutions-APIG3",
                    reason="WAF is not required for this development API"
                ),
                NagPackSuppression(
                    id="AwsSolutions-APIG6",
                    reason="CloudWatch logging for all methods is not required for this development API"
                )
            ]
        )

        NagSuppressions.add_resource_suppressions(
            construct=root_method,
            apply_to_children=True,
            suppressions=[
                {
                    "id": "AwsSolutions-APIG4",
                    "reason": "Authorization is not required for this public endpoint"
                },
                {
                    "id": "AwsSolutions-COG4",
                    "reason": "Cognito user pool authorizer is not required for this public endpoint"
                }
            ]
        )

        NagSuppressions.add_resource_suppressions(
            construct=get_profiles,
            apply_to_children=True,
            suppressions=[
                {
                    "id": "AwsSolutions-APIG4",
                    "reason": "Authorization is not required for this public endpoint"
                },
                {
                    "id": "AwsSolutions-COG4",
                    "reason": "Cognito user pool authorizer is not required for this public endpoint"
                }
            ]
        )

        NagSuppressions.add_resource_suppressions(
            construct=get_profile_id,
            apply_to_children=True,
            suppressions=[
                {
                    "id": "AwsSolutions-APIG4",
                    "reason": "Authorization is not required for this public endpoint"
                },
                {
                    "id": "AwsSolutions-COG4",
                    "reason": "Cognito user pool authorizer is not required for this public endpoint"
                }
            ]
        )
