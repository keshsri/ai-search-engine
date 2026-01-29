import uuid
from typing import Optional
import logging

from app.models.document import Document
from app.db.dynamodb import DynamoDBClient
from app.services.chunking_service import ChunkingService
from app.services.dummy_embedding_service import DummyEmbeddingService
from app.vector_store.faiss_store import FAISSVectorStore
from app.core.config import settings
from app.db.chunks_dynamodb import ChunksDynamoDB

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self):
        self.db = DynamoDBClient()
        self.chunker = ChunkingService(chunk_size=settings.CHUNK_SIZE)
        self.embedding_service = DummyEmbeddingService(dimension=settings.EMBEDDING_DIMENSION)
        self.vector_store = FAISSVectorStore(dimension=settings.EMBEDDING_DIMENSION)
        self.chunks_db = ChunksDynamoDB()

    def ingest(self, document: Document) -> Document:
        document.id = document.id or str(uuid.uuid4())

        item = {
            "document_id": document.id,
            "title": document.title,
            "content": document.content,
            "source": document.source,
            "created_at": document.created_at.isoformat()
        }

        chunks = self.chunker.chunk_text(document.id, document.content)
        logger.info(f"Created {len(chunks)} chunks for document {document.id}")

        if chunks:
            self.chunks_db.save_chunks(chunks)

        self.db.table.put_item(Item=item)
        return document

    def get_by_id(self, document_id: str) -> Optional[Document]:
        response = self.db.table.get_item(
            Key={"document_id": document_id}
        )

        item = response.get("Item")
        if not item:
            return None

        return Document(
            id = item["document_id"],
            title = item["title"],
            content = item["content"],
            source = item.get("source"),
            created_at = item["created_at"]
        )
