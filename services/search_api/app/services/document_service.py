import uuid
from typing import Optional
import logging
import numpy as np
from botocore.exceptions import ClientError

from app.models.document import Document
from app.db.dynamodb import DynamoDBClient
from app.db.chunks_dynamodb import ChunksDynamoDB
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.vector_store.faiss_vector_store import FAISSVectorStore
from app.core.config import settings
from app.core.exceptions import (
    DocumentNotFoundException,
    EmptyDocumentException,
    DatabaseException,
)

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
        logger.info(f"Starting document ingestion: document_id={document.id}, title='{document.title}'")
        logger.debug(f"Document content length: {len(document.content)} characters")

        # Validate document has content
        if not document.content or not document.content.strip():
            logger.warning(f"Document has no content: document_id={document.id}")
            raise EmptyDocumentException(
                message="Document has no extractable content",
                details={"document_id": document.id, "title": document.title}
            )

        item = {
            "document_id": document.id,
            "title": document.title,
            "content": document.content,
            "source": document.source,
            "created_at": document.created_at.isoformat()
        }

        try:
            self.db.table.put_item(Item=item)
            logger.info(f"Saved document metadata to DynamoDB: document_id={document.id}")
        except ClientError as e:
            logger.error(f"DynamoDB ClientError saving document: document_id={document.id}, error={str(e)}")
            raise DatabaseException(
                message="Failed to save document metadata",
                details={"document_id": document.id, "error": str(e)}
            )
        except Exception as e:
            logger.error(f"Unexpected error saving document to DynamoDB: document_id={document.id}, error={str(e)}")
            raise DatabaseException(
                message="Failed to save document",
                details={"document_id": document.id, "error": str(e)}
            )

        logger.debug(f"Starting chunking for document_id={document.id}")
        chunks = self.chunker.chunk_text(document.id, document.content)
        logger.info(f"Created {len(chunks)} chunks for document {document.id}")

        if not chunks:
            logger.warning(f"No chunks created for document_id={document.id}, skipping embedding and vector storage")
            return document

        try:
            self.chunks_db.save_chunks(chunks)
            logger.info(f"Saved {len(chunks)} chunks to DynamoDB for document_id={document.id}")
        except DatabaseException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving chunks: document_id={document.id}, error={str(e)}")
            raise DatabaseException(
                message="Failed to save document chunks",
                details={"document_id": document.id, "error": str(e)}
            )

        logger.debug(f"Generating embeddings for {len(chunks)} chunks")
        texts = [chunk.content for chunk in chunks]
        vectors = self.embedding_service.embed(texts)
        logger.info(f"Generated {len(vectors)} embeddings for document_id={document.id}")
        
        # Convert to numpy array for FAISS
        vectors_np = np.array(vectors).astype('float32')
        logger.debug(f"Converted embeddings to numpy array: shape={vectors_np.shape}")

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
        logger.info(f"Stored {len(vectors)} vectors in FAISS for document_id={document.id}")

        logger.info(f"Successfully completed ingestion for document_id={document.id}")
        return document

    def get_by_id(self, document_id: str) -> Optional[Document]:
        logger.debug(f"Retrieving document from DynamoDB: document_id={document_id}")
        
        try:
            response = self.db.table.get_item(
                Key={"document_id": document_id}
            )
        except ClientError as e:
            logger.error(f"DynamoDB ClientError retrieving document: document_id={document_id}, error={str(e)}")
            raise DatabaseException(
                message="Failed to retrieve document",
                details={"document_id": document_id, "error": str(e)}
            )
        except Exception as e:
            logger.error(f"Unexpected error retrieving document from DynamoDB: document_id={document_id}, error={str(e)}")
            raise DatabaseException(
                message="Failed to retrieve document",
                details={"document_id": document_id, "error": str(e)}
            )

        item = response.get("Item")
        if not item:
            logger.warning(f"Document not found: document_id={document_id}")
            raise DocumentNotFoundException(
                message=f"Document not found",
                details={"document_id": document_id}
            )

        logger.info(f"Successfully retrieved document: document_id={document_id}, title='{item.get('title')}'")
        return Document(
            id=item["document_id"],
            title=item["title"],
            content=item["content"],
            source=item.get("source"),
            created_at=item["created_at"],
        )
