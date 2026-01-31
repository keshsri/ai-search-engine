import boto3
import os
import logging
from typing import List
from botocore.exceptions import ClientError, BotoCoreError

from app.models.chunk import Chunk
from app.core.exceptions import DatabaseException

logger = logging.getLogger(__name__)

CHUNKS_TABLE_NAME = os.getenv("CHUNKS_TABLE_NAME", "document_chunks")

dynamodb = boto3.resource("dynamodb")

class ChunksDynamoDB:
    def __init__(self):
        logger.info(f"Initializing ChunksDynamoDB with table: {CHUNKS_TABLE_NAME}")
        try:
            self.table = dynamodb.Table(CHUNKS_TABLE_NAME)
            logger.info(f"Successfully connected to DynamoDB chunks table: {CHUNKS_TABLE_NAME}")
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to initialize ChunksDynamoDB: {str(e)}")
            raise DatabaseException(
                message="Failed to connect to chunks table",
                details={"table": CHUNKS_TABLE_NAME, "error": str(e)}
            )
        except Exception as e:
            logger.error(f"Unexpected error initializing ChunksDynamoDB: {str(e)}")
            raise DatabaseException(
                message="Failed to initialize chunks database client",
                details={"error": str(e)}
            )

    def save_chunks(self, chunks: List[Chunk]) -> None:
        if not chunks:
            logger.warning("Empty chunks list provided, skipping save operation")
            return

        logger.info(f"Saving {len(chunks)} chunks to DynamoDB table: {CHUNKS_TABLE_NAME}")
        logger.debug(f"First chunk document_id: {chunks[0].document_id}")

        try:
            with self.table.batch_writer() as batch:
                for i, chunk in enumerate(chunks):
                    batch.put_item(
                        Item = {
                            "document_id": chunk.document_id,
                            "chunk_id": chunk.chunk_id,
                            "index": chunk.index,
                            "content": chunk.content,
                            "created_at": chunk.created_at.isoformat(),
                        }
                    )
                    if (i + 1) % 25 == 0:  # Log progress every 25 chunks
                        logger.debug(f"Saved {i + 1}/{len(chunks)} chunks")
            
            logger.info(f"Successfully saved all {len(chunks)} chunks to DynamoDB")
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to save chunks to DynamoDB: {str(e)}")
            raise DatabaseException(
                message="Failed to save chunks to database",
                details={"chunk_count": len(chunks), "error": str(e)}
            )
        except Exception as e:
            logger.error(f"Unexpected error saving chunks to DynamoDB: {str(e)}")
            raise DatabaseException(
                message="Failed to save chunks",
                details={"error": str(e)}
            )