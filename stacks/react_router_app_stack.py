import json
from aws_cdk import (
    CfnOutput,
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda_event_sources as event_source,
    aws_cloudfront_origins as origins,
    aws_cloudfront as cloudfront,
    aws_s3_deployment as s3deploy,
    RemovalPolicy)
from constructs import Construct
from cdk_nag import NagSuppressions, NagPackSuppression
import os.path
dirname = os.path.dirname(__file__)

class ReactRouterAppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        hosting_bucket = s3.Bucket(
            self,
            'react-router-app-hostbucket',
            removal_policy=RemovalPolicy.DESTROY,  # DESTROY for development; use RETAIN for production
            auto_delete_objects=True,  # Clean up objects when bucket is removed (for development)
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # Make the bucket completely private
            access_control=s3.BucketAccessControl.PRIVATE,  # Set access control to private
            encryption=s3.BucketEncryption.S3_MANAGED,  # Enable encryption
            enforce_ssl=True  # Enforce SSL for bucket access
        
        )

        react_app_distribution = cloudfront.Distribution(
            self,
            'react-router-app-cdnDistro',
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(hosting_bucket, origin_access_levels=[cloudfront.AccessLevel.READ, cloudfront.AccessLevel.READ_VERSIONED, cloudfront.AccessLevel.WRITE, cloudfront.AccessLevel.DELETE]),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN
            ),
            default_root_object='index.html',
            enable_logging=False,
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
            price_class=cloudfront.PriceClass.PRICE_CLASS_100
        )

        hosting_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[hosting_bucket.arn_for_objects("*")],
                principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{react_app_distribution.distribution_id}"
                    }
                }
            )
        )

        # Deploy the React app to S3
        deployment = s3deploy.BucketDeployment(
            self, 'DeployReactApp',
            sources=[s3deploy.Source.asset(os.path.join(os.path.dirname(__file__), '../vite-tanstack-router-app/dist'))],
            destination_bucket=hosting_bucket,
            distribution=react_app_distribution,
            distribution_paths=['/*']  # Invalidate all cached files after deployment
        )

        #Suppressions

        # 1. Suppress S3 bucket server access logs warning
        NagSuppressions.add_resource_suppressions(
            hosting_bucket,
            suppressions=[
                NagPackSuppression(
                    id="AwsSolutions-S1",
                    reason="Server access logs disabled for dev environment. Will be enabled in production."
                )
            ]
        )

        # 2. Suppress CloudFront distribution warnings and errors
        NagSuppressions.add_resource_suppressions(
            react_app_distribution,
            suppressions=[
                NagPackSuppression(
                    id="AwsSolutions-CFR1",
                    reason="Geo restrictions not required for this application as it's globally accessible by design."
                ),
                NagPackSuppression(
                    id="AwsSolutions-CFR2",
                    reason="WAF integration will be implemented in production environment, not required for development."
                ),
                NagPackSuppression(
                    id="AwsSolutions-CFR3",
                    reason="Access logging disabled for development environment to reduce costs. Will be enabled in production."
                ),
                NagPackSuppression(
                    id="AwsSolutions-CFR4",
                    reason="Using TLSv1.2 which is sufficient for our security requirements."
                )
            ]
        )

        # 3. Suppress BucketDeployment construct IAM errors
        custom_resource_construct = deployment.node.find_child("CustomResourceHandler")
        if custom_resource_construct:
            NagSuppressions.add_resource_suppressions(
                custom_resource_construct,
                apply_to_children=True,
                suppressions=[
                    NagPackSuppression(
                        id="AwsSolutions-IAM5",
                        reason="CDK BucketDeployment uses wildcard permissions for S3 operations, which is required for deployment functionality."
                    )
                ]
            )

        # 4. Suppress the Lambda CDK BucketDeployment service role IAM errors
        bucket_deployment_construct = self.node.find_child("Custom::CDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756C")
        if bucket_deployment_construct:
            service_role = bucket_deployment_construct.node.find_child("ServiceRole")
            NagSuppressions.add_resource_suppressions(
                service_role,
                apply_to_children=True,
                suppressions=[
                    NagPackSuppression(
                        id="AwsSolutions-IAM4",
                        reason="AWS Lambda Basic Execution Role is required for Lambda to write logs to CloudWatch."
                    ),
                    NagPackSuppression(
                        id="AwsSolutions-IAM5",
                        reason="CDK BucketDeployment requires these S3 permissions to deploy assets from source to destination bucket."
                    )
                ]
            )
            
            # Suppress Lambda runtime warning
            NagSuppressions.add_resource_suppressions(
                bucket_deployment_construct,
                suppressions=[
                    NagPackSuppression(
                        id="AwsSolutions-L1",
                        reason="Using CDK provided Lambda runtime which is managed by AWS CDK team."
                    )
                ]
            )

        # 5. Add stack-level suppressions for any remaining resources that might be harder to target directly
        NagSuppressions.add_stack_suppressions(
            self,
            suppressions=[
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "Wildcard permissions required by CDK BucketDeployment custom resource.",
                    "applies_to": [
                        "Resource::*", 
                        "Action::s3:GetBucket*",
                        "Action::s3:GetObject*",
                        "Action::s3:List*",
                        "Action::s3:Abort*",
                        "Action::s3:DeleteObject*"
                    ]
                },
                {
                    "id": "AwsSolutions-L1",
                    "reason": "Using CDK provided Lambda runtime which is managed by AWS CDK team."
                }
            ]
        )

        # Output the CloudFront URL
        CfnOutput(
            self, 'CloudFrontURL',
            value=f'https://{react_app_distribution.distribution_domain_name}'
        )





