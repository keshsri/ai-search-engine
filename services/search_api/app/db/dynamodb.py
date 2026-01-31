import boto3
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class DynamoDBClient:
    def __init__(self):
        self.region = settings.AWS_REGION
        self.table_name = settings.DYNAMODB_DOCUMENT_TABLE

        logger.info(f"Initializing DynamoDBClient: region={self.region}, table={self.table_name}")

        try:
            self.resource = boto3.resource(
                "dynamodb",
                region_name=self.region
            )

            self.table = self.resource.Table(self.table_name)
            logger.info(f"Successfully connected to DynamoDB table: {self.table_name}")
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB client: {str(e)}")
            raise
