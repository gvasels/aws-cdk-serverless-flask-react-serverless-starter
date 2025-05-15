from typing import Any

from aws_cdk import (
    Stack,
    CfnOutput
)

from constructs import Construct

from app_components.shared.identity.infrastructure import Identity


class SharedServices(Stack):
    def __init__(
        self,
        scope: Construct,
        id_: str,
        **kwargs: Any,
    ):
        super().__init__(scope, id_, **kwargs)

        identity = Identity(
            self,
            "Identity",
        )

        # Export the user pool ARN
        self.user_pool_arn_output = CfnOutput(
            self, "UserPoolArn",
            value=identity.user_pool.user_pool_arn,
            export_name="CognitoUserPoolArn"
        )
        
        # Export the user pool ID as well
        self.user_pool_id_output = CfnOutput(
            self, "UserPoolId",
            value=identity.user_pool.user_pool_id,
            export_name="CognitoUserPoolId"
        )
