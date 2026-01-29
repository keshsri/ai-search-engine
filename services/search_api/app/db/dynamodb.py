import boto3
from app.core.config import settings


class DynamoDBClient:
    def __init__(self):
        self.region = settings.AWS_REGION
        self.table_name = settings.DYNAMODB_DOCUMENT_TABLE

        self.resource = boto3.resource(
            "dynamodb",
            region_name=self.region
        )

        self.table = self.resource.Table(self.table_name)
