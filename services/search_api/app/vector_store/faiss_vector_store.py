import faiss
import numpy as np
import os
import json
from typing import List, Dict
import logging
import boto3
from botocore.exceptions import ClientError

from app.core.exceptions import VectorStoreException
from app.core.config import settings

logger = logging.getLogger(__name__)

class FAISSVectorStore:
    def __init__(self, dim: int, index_path: str = "faiss.index", metadata_path: str = "faiss_meta.json"):
        self.dim = dim
        self.index_path = index_path
        self.metadata_path = metadata_path
        
        # S3 configuration
        self.use_s3 = os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None
        if self.use_s3:
            self.s3_client = boto3.client('s3')
            self.s3_bucket = os.environ.get('DOCUMENTS_BUCKET')
            self.s3_index_key = os.environ.get('FAISS_INDEX_S3_KEY', 'faiss/index.faiss')
            self.s3_metadata_key = os.environ.get('FAISS_METADATA_S3_KEY', 'faiss/metadata.json')
            # Use /tmp for local cache in Lambda
            self.index_path = f"/tmp/{os.path.basename(index_path)}"
            self.metadata_path = f"/tmp/{os.path.basename(metadata_path)}"
            logger.info(f"Running in Lambda, using S3 bucket: {self.s3_bucket}")
        else:
            self.s3_client = None
            logger.info("Running locally, using local file storage")

        logger.info(f"Initializing FAISSVectorStore: dim={dim}, index_path={self.index_path}, metadata_path={self.metadata_path}")
        self.index = self._load_or_create_index()
        self.metadata = self._load_metadata()
        logger.info(f"FAISS index initialized with {self.index.ntotal} vectors and {len(self.metadata)} metadata entries")

    def _download_from_s3(self, s3_key: str, local_path: str) -> bool:
        """Download file from S3 to local path. Returns True if successful."""
        try:
            logger.info(f"Downloading {s3_key} from S3 bucket {self.s3_bucket} to {local_path}")
            self.s3_client.download_file(self.s3_bucket, s3_key, local_path)
            logger.info(f"Successfully downloaded {s3_key} from S3")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.info(f"File {s3_key} not found in S3 (first time setup)")
                return False
            else:
                logger.error(f"Failed to download {s3_key} from S3: {str(e)}")
                raise VectorStoreException(
                    message="Failed to download from S3",
                    details={"s3_key": s3_key, "error": str(e)}
                )
        except Exception as e:
            logger.error(f"Unexpected error downloading {s3_key} from S3: {str(e)}")
            raise VectorStoreException(
                message="Failed to download from S3",
                details={"s3_key": s3_key, "error": str(e)}
            )

    def _upload_to_s3(self, local_path: str, s3_key: str):
        """Upload file from local path to S3."""
        try:
            logger.info(f"Uploading {local_path} to S3 bucket {self.s3_bucket} as {s3_key}")
            self.s3_client.upload_file(local_path, self.s3_bucket, s3_key)
            logger.info(f"Successfully uploaded {s3_key} to S3")
        except Exception as e:
            logger.error(f"Failed to upload {s3_key} to S3: {str(e)}")
            raise VectorStoreException(
                message="Failed to upload to S3",
                details={"s3_key": s3_key, "error": str(e)}
            )

    def _load_or_create_index(self):
        # Try to load from S3 if in Lambda
        if self.use_s3:
            self._download_from_s3(self.s3_index_key, self.index_path)
        
        if os.path.exists(self.index_path):
            logger.info(f"Loading existing FAISS index from {self.index_path}")
            try:
                index = faiss.read_index(self.index_path)
                logger.info(f"Successfully loaded FAISS index with {index.ntotal} vectors")
                return index
            except Exception as e:
                logger.error(f"Failed to load FAISS index from {self.index_path}: {str(e)}")
                raise VectorStoreException(
                    message="Failed to load vector index",
                    details={"index_path": self.index_path, "error": str(e)}
                )
        else:
            logger.info(f"Creating new FAISS IndexFlatIP with dimension {self.dim}")
            try:
                return faiss.IndexFlatIP(self.dim)
            except Exception as e:
                logger.error(f"Failed to create FAISS index: {str(e)}")
                raise VectorStoreException(
                    message="Failed to create vector index",
                    details={"dimension": self.dim, "error": str(e)}
                )

    def _load_metadata(self) -> List[Dict]:
        # Try to load from S3 if in Lambda
        if self.use_s3:
            self._download_from_s3(self.s3_metadata_key, self.metadata_path)
        
        if os.path.exists(self.metadata_path):
            logger.info(f"Loading metadata from {self.metadata_path}")
            try:
                with open(self.metadata_path, "r") as f:
                    metadata = json.load(f)
                logger.info(f"Successfully loaded {len(metadata)} metadata entries")
                return metadata
            except Exception as e:
                logger.error(f"Failed to load metadata from {self.metadata_path}: {str(e)}")
                raise VectorStoreException(
                    message="Failed to load vector metadata",
                    details={"metadata_path": self.metadata_path, "error": str(e)}
                )
        else:
            logger.info("No existing metadata file found, starting with empty metadata")
            return []

    def add(self, vectors: np.ndarray, metadatas: List[Dict]):
        if len(vectors) == 0:
            logger.warning("Attempted to add empty vector array, skipping")
            return

        logger.debug(f"Adding {len(vectors)} vectors to FAISS index")
        logger.debug(f"Vector shape: {vectors.shape}, expected dimension: {self.dim}")

        if vectors.shape[1] != self.dim:
            error_msg = f"Vector dimension mismatch: got {vectors.shape[1]}, expected {self.dim}"
            logger.error(error_msg)
            raise VectorStoreException(
                message="Vector dimension mismatch",
                details={"expected": self.dim, "received": vectors.shape[1]}
            )

        try:
            previous_count = self.index.ntotal
            self.index.add(vectors)
            self.metadata.extend(metadatas)
            logger.info(f"Added {len(vectors)} vectors to FAISS index (total: {previous_count} -> {self.index.ntotal})")
            
            self._persist()
        except VectorStoreException:
            raise
        except Exception as e:
            logger.error(f"Failed to add vectors to FAISS index: {str(e)}")
            raise VectorStoreException(
                message="Failed to add vectors to index",
                details={"vector_count": len(vectors), "error": str(e)}
            )

    def search(self, query_vector: np.ndarray, top_k: int = 5):
        if self.index.ntotal == 0:
            logger.warning("Search attempted on empty FAISS index, returning empty results")
            return []

        logger.debug(f"Searching FAISS index for top {top_k} results (total vectors: {self.index.ntotal})")
        logger.debug(f"Query vector shape: {query_vector.shape}")

        try:
            scores, indices = self.index.search(query_vector, top_k)
            logger.debug(f"FAISS search returned scores: {scores[0]}, indices: {indices[0]}")

            results = []
            for idx in indices[0]:
                if idx == -1:
                    logger.debug("Encountered -1 index (no match), skipping")
                    continue
                if idx >= len(self.metadata):
                    logger.warning(f"Index {idx} out of bounds for metadata (size: {len(self.metadata)})")
                    continue
                results.append(self.metadata[idx])

            logger.info(f"Search completed: found {len(results)} results out of {top_k} requested")
            return results
        except Exception as e:
            logger.error(f"Failed to search FAISS index: {str(e)}")
            raise VectorStoreException(
                message="Failed to search vector index",
                details={"top_k": top_k, "error": str(e)}
            )

    def _persist(self):
        logger.debug(f"Persisting FAISS index to {self.index_path} and metadata to {self.metadata_path}")
        try:
            # Save locally first
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, "w") as f:
                json.dump(self.metadata, f, indent=2)
            logger.info(f"Successfully persisted FAISS index ({self.index.ntotal} vectors) and {len(self.metadata)} metadata entries locally")
            
            # Upload to S3 if in Lambda
            if self.use_s3:
                self._upload_to_s3(self.index_path, self.s3_index_key)
                self._upload_to_s3(self.metadata_path, self.s3_metadata_key)
                logger.info("Successfully uploaded FAISS index and metadata to S3")
        except VectorStoreException:
            raise
        except Exception as e:
            logger.error(f"Failed to persist FAISS index or metadata: {str(e)}")
            raise VectorStoreException(
                message="Failed to persist vector index",
                details={"index_path": self.index_path, "metadata_path": self.metadata_path, "error": str(e)}
            )
