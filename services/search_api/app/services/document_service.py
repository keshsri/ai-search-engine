import uuid
from typing import Optional
import logging
import numpy as np
from botocore.exceptions import ClientError

from app.models.document import Document
from app.db.dynamodb import DynamoDBClient
from app.db.chunks_dynamodb import ChunksDynamoDB
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import get_embedding_service
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
        self.embedding_service = get_embedding_service()
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

        # Calculate TTL: 15 days from now (in Unix timestamp)
        import time
        ttl = int(time.time()) + (15 * 24 * 60 * 60)  # 15 days in seconds

        item = {
            "document_id": document.id,
            "title": document.title,
            "content": document.content,
            "source": document.source,
            "created_at": document.created_at.isoformat(),
            "ttl": ttl  # Auto-delete after 15 days
        }

        try:
            self.db.table.put_item(Item=item)
            logger.info(f"Saved document metadata to DynamoDB: document_id={document.id}, ttl={ttl}")
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

    def delete(self, document_id: str) -> bool:
        """
        Delete a document and all associated data.
        
        Deletes:
        - Document metadata from DynamoDB
        - All chunks from DynamoDB  
        - Vectors from FAISS index
        - Raw file from S3 (if file_type is stored)
        
        Args:
            document_id: Document ID to delete
        
        Returns:
            bool: True if document was found and deleted, False if not found
        """
        logger.info(f"Starting deletion for document_id={document_id}")
        
        # Check if document exists
        try:
            document = self.get_by_id(document_id)
        except DocumentNotFoundException:
            logger.warning(f"Document not found for deletion: {document_id}")
            return False
        
        deleted_any = False
        
        # 1. Delete chunks from DynamoDB
        try:
            logger.info(f"Deleting chunks for document_id={document_id}")
            self.chunks_db.delete_by_document_id(document_id)
            logger.info(f"Successfully deleted chunks for document_id={document_id}")
            deleted_any = True
        except Exception as e:
            logger.error(f"Failed to delete chunks for document_id={document_id}: {str(e)}")
        
        # 2. Delete vectors from FAISS
        try:
            logger.info(f"Deleting vectors for document_id={document_id}")
            self.vector_store.delete_by_document_id(document_id)
            logger.info(f"Successfully deleted vectors for document_id={document_id}")
            deleted_any = True
        except Exception as e:
            logger.error(f"Failed to delete vectors for document_id={document_id}: {str(e)}")
        
        # 3. Delete raw file from S3 (if file_type is available)
        if hasattr(document, 'file_type') and document.file_type:
            try:
                from app.services.file_storage import FileStorage
                file_storage = FileStorage()
                logger.info(f"Deleting raw file for document_id={document_id}")
                file_storage.delete(document_id, document.file_type)
                logger.info(f"Successfully deleted raw file for document_id={document_id}")
                deleted_any = True
            except Exception as e:
                logger.error(f"Failed to delete raw file for document_id={document_id}: {str(e)}")
        
        # 4. Delete document metadata from DynamoDB (do this last)
        try:
            logger.info(f"Deleting document metadata for document_id={document_id}")
            self.db.table.delete_item(Key={"document_id": document_id})
            logger.info(f"Successfully deleted document metadata for document_id={document_id}")
            deleted_any = True
        except ClientError as e:
            logger.error(f"Failed to delete document metadata for document_id={document_id}: {str(e)}")
            raise DatabaseException(
                message="Failed to delete document metadata",
                details={"document_id": document_id, "error": str(e)}
            )
        
        logger.info(f"Completed deletion for document_id={document_id}")
        return deleted_any
