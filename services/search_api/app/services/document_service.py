import uuid
from typing import Optional
import logging
import numpy as np

from app.models.document import Document
from app.db.dynamodb import DynamoDBClient
from app.db.chunks_dynamodb import ChunksDynamoDB
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.vector_store.faiss_vector_store import FAISSVectorStore
from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, vector_store: FAISSVectorStore):
        self.db = DynamoDBClient()
        self.chunks_db = ChunksDynamoDB()
        self.chunker = ChunkingService(chunk_size=settings.CHUNK_SIZE)
        self.embedding_service = EmbeddingService()
        self.vector_store = vector_store

    def ingest(self, document: Document) -> Document:
        document.id = document.id or str(uuid.uuid4())

        item = {
            "document_id": document.id,
            "title": document.title,
            "content": document.content,
            "source": document.source,
            "created_at": document.created_at.isoformat()
        }

        self.db.table.put_item(Item=item)

        chunks = self.chunker.chunk_text(document.id, document.content)
        logger.info(f"Created {len(chunks)} chunks for document {document.id}")

        if not chunks:
            return document

        self.chunks_db.save_chunks(chunks)

        texts = [chunk.content for chunk in chunks]
        vectors = self.embedding_service.embed(texts)
        
        # Convert to numpy array for FAISS
        vectors_np = np.array(vectors).astype('float32')

        metadata = [
            {
                "document_id": chunk.document_id,
                "chunk_id": chunk.chunk_id,
                "index": chunk.index,
                "content": chunk.content,
            }
            for chunk in chunks
        ]

        # Store in FAISS
        self.vector_store.add(vectors_np, metadata)

        logger.info(f"Stored {len(vectors)} vectors in FAISS")

        return document

    def get_by_id(self, document_id: str) -> Optional[Document]:
        response = self.db.table.get_item(
            Key={"document_id": document_id}
        )

        item = response.get("Item")
        if not item:
            return None

        return Document(
            id=item["document_id"],
            title=item["title"],
            content=item["content"],
            source=item.get("source"),
            created_at=item["created_at"],
        )
