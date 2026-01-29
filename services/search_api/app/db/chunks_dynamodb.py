import boto3
import os
from typing import List
from app.models.chunk import Chunk

CHUNKS_TABLE_NAME = os.getenv("CHUNKS_TABLE_NAME", "document_chunks")

dynamodb = boto3.resource("dynamodb")

class ChunksDynamoDB:
    def __init__(self):
        self.table = dynamodb.Table(CHUNKS_TABLE_NAME)

    def save_chunks(self, chunks: List[Chunk]) -> None:
        if not chunks:
            return

        with self.table.batch_writer() as batch:
            for chunk in chunks:
                batch.put_item(
                    Item = {
                        "document_id": chunk.document_id,
                        "chunk_id": chunk.chunk_id,
                        "index": chunk.index,
                        "content": chunk.content,
                        "created_at": chunk.created_at.isoformat(),
                    }
                )