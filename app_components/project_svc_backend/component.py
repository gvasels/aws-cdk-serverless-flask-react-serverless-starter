from typing import Any

from aws_cdk import (
    Stack,
    CfnOutput
)

from constructs import Construct

from app_components.project_svc_backend.api.infrastructure import ProjectAPI
from app_components.project_svc_backend.database.infrastructure import ProjectDatabase


class ProjectBackend(Stack):
    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        dynamodb_table_name: str,
        **kwargs: Any,
    ):
        super().__init__(scope, id_, **kwargs)

        database = ProjectDatabase(
            self,
            "Database",
        )
        api = ProjectAPI(
            self,
            "API",
            dynamodb_table_name=dynamodb_table_name,#database.dynamodb_table.table_name
            region_name=Stack.of(self).region,
            account_id=Stack.of(self).account,
        )
        #Monitoring(self, "Monitoring", database=database, api=api)

        #database.dynamodb_table.grant_read_write_data(api.lambda_function)

        self.api_endpoint = CfnOutput(
            self,
            "APIEndpoint",
            # API doesn't disable create_default_stage, hence URL will be defined
            value=api.app_layer_api.url,  # type: ignore
        )

        self.project_backend_lambda = CfnOutput(
            self,
            "ProjectBackendLambda",
            value=api.api_svc_lambda.function_name
        )


