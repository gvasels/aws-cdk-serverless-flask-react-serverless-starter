from typing import Any

from aws_cdk import (
    Stack,
    CfnOutput
)

from constructs import Construct
from cdk_nag import NagSuppressions, NagPackSuppression

from app_components.frontend.hosting.infrastructure import HostedWebApp


class FrontEndHosting(Stack):
    def __init__(
        self,
        scope: Construct,
        id_: str,
        **kwargs: Any,
    ):
        super().__init__(scope, id_, **kwargs)

        frontend = HostedWebApp(
            self,
            "Identity",
        )

         # Output the CloudFront URL
        self.cloudfront_url = CfnOutput(
            self, 'CloudFrontURL',
            value=f'https://{frontend.react_app_distribution.distribution_domain_name}'
        )

        self.user_app_client_name = CfnOutput(
            self, 'UserAppClientName',
            value=frontend.app_client.user_pool_client_name
        )
        
        self.user_app_client_id = CfnOutput(
            self, 'UserAppClientId',
            value=frontend.app_client.user_pool_client_id
        )
        
        # Suppress the Lambda runtime warning for CDK BucketDeployment
        NagSuppressions.add_resource_suppressions_by_path(
            self,
            "/FrontEndHostingSandbox/Custom::CDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756C/Resource",
            [
                NagPackSuppression(
                    id="AwsSolutions-L1",
                    reason="CDK BucketDeployment uses a managed Lambda runtime that we cannot control"
                )
            ]
        )


