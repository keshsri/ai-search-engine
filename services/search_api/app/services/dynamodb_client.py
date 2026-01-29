import boto3
import os

class DynamoDBClient:
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.table_name = os.getenv("DOCUMENTS_TABLE_NAME", "ai-search-documents")

        self.resource = boto3.resource(
            "dynamodb",
            region_name = self.region
        )

        self.table = self.resource.Table(self.table_name)