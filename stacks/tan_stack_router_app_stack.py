import json
from aws_cdk import (
    CfnOutput,
    Stack,
    Duration,
    Fn,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda_event_sources as event_source,
    aws_cloudfront_origins as origins,
    aws_cloudfront as cloudfront,
    aws_s3_deployment as s3deploy,
    RemovalPolicy,
    aws_cognito as cognito)
from constructs import Construct
from cdk_nag import NagSuppressions, NagPackSuppression
import os.path
dirname = os.path.dirname(__file__)

class TanStackRouterStack(Stack):

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
        react_app_domain_name = react_app_distribution.distribution_domain_name
        shared_user_pool_arn = Fn.import_value("CognitoUserPoolArn")

        # Create an app client which should be used by the react application
        shared_user_pool = cognito.UserPool.from_user_pool_arn(
            self, "ExistingUserPool", shared_user_pool_arn
        )

        # Create the app client with the specified token settings
        app_client = shared_user_pool.add_client(
            "serverless-starter-app-client",
            user_pool_client_name="serverless-starter-app-client",
            
            # Set token validity durations
            access_token_validity=Duration.days(1),     # 1 day for access token
            id_token_validity=Duration.days(1),         # 1 day for ID token
            refresh_token_validity=Duration.days(3650), # 10 years for refresh token
            
            # Enable authentication flows - user password and SRP for web app login
            auth_flows=cognito.AuthFlow(
                user_password=True,  # Allow plain email/password login
                user_srp=True       # More secure login using SRP protocol
            ),
            
            # Don't generate a secret for public web applications
            generate_secret=False,  # Web applications typically don't use a client secret
            
            # Prevent user existence errors for security
            prevent_user_existence_errors=True,
            
            # OAuth settings for web application
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    implicit_code_grant=True,  # For web apps to get tokens directly
                    authorization_code_grant=True  # Recommended for web apps
                ),
                scopes=[
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PROFILE
                ],
                # Update these URLs with your actual web app URLs
                callback_urls=[
                    f"https://{react_app_domain_name}/", 
                    "http://localhost:5173"  # For local development
                ],
                logout_urls=[
                    f"https://{react_app_domain_name}/", 
                    "http://localhost:3000/"  # For local development
                ]
            ),
            
            # Support username-password based authentication
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO
            ]
        )

        # Create a custom IAM role for the BucketDeployment with CloudFront invalidation permissions
        deployment_role = iam.Role(
            self, 'CloudFrontInvalidationRole',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com')
        )
        
        # Add CloudFront invalidation permissions
        deployment_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudfront:GetInvalidation",
                    "cloudfront:CreateInvalidation"
                ],
                resources=["*"]
            )
        )
        
        # Add basic Lambda execution permissions
        deployment_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')
        )
        
        # Add S3 permissions needed for deployment
        deployment_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject*",
                    "s3:GetBucket*",
                    "s3:List*",
                    "s3:DeleteObject*",
                    "s3:PutObject*",
                    "s3:Abort*"
                ],
                resources=[
                    hosting_bucket.bucket_arn,
                    f"{hosting_bucket.bucket_arn}/*"
                ]
            )
        )
        
        # Deploy the React app to S3 with the custom role
        deployment = s3deploy.BucketDeployment(
            self, 'DeployReactApp',
            sources=[s3deploy.Source.asset(os.path.join(os.path.dirname(__file__), '../vite-tanstack-router-app/dist'))],
            destination_bucket=hosting_bucket,
            distribution=react_app_distribution,
            distribution_paths=['/*'],  # Invalidate all cached files after deployment
            prune=False,  # Don't delete files that no longer exist in the source
            role=deployment_role  # Use our custom role with CloudFront permissions
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
        # Apply suppressions directly to our custom role
        NagSuppressions.add_resource_suppressions(
            deployment_role,
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
        
        # Try to find the bucket deployment construct for Lambda runtime suppression
        for child in self.node.children:
            if "CDKBucketDeployment" in child.node.id:
                NagSuppressions.add_resource_suppressions(
                    child,
                    suppressions=[
                        NagPackSuppression(
                            id="AwsSolutions-L1",
                            reason="Using CDK provided Lambda runtime which is managed by AWS CDK team."
                        )
                    ]
                )
                break

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
                        "Action::s3:DeleteObject*",
                        "Action::cloudfront:GetInvalidation",
                        "Action::cloudfront:CreateInvalidation"
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





