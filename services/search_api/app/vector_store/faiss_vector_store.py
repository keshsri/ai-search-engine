import faiss
import numpy as np
import os
import json
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class FAISSVectorStore:
    def __init__(self, dim: int, index_path: str = "faiss.index", metadata_path: str = "faiss_meta.json"):
        self.dim = dim
        self.index_path = index_path
        self.metadata_path = metadata_path

        logger.info(f"Initializing FAISSVectorStore: dim={dim}, index_path={index_path}, metadata_path={metadata_path}")
        self.index = self._load_or_create_index()
        self.metadata = self._load_metadata()
        logger.info(f"FAISS index initialized with {self.index.ntotal} vectors and {len(self.metadata)} metadata entries")

    def _load_or_create_index(self):
        if os.path.exists(self.index_path):
            logger.info(f"Loading existing FAISS index from {self.index_path}")
            try:
                index = faiss.read_index(self.index_path)
                logger.info(f"Successfully loaded FAISS index with {index.ntotal} vectors")
                return index
            except Exception as e:
                logger.error(f"Failed to load FAISS index from {self.index_path}: {str(e)}")
                raise
        else:
            logger.info(f"Creating new FAISS IndexFlatIP with dimension {self.dim}")
            return faiss.IndexFlatIP(self.dim)

    def _load_metadata(self) -> List[Dict]:
        if os.path.exists(self.metadata_path):
            logger.info(f"Loading metadata from {self.metadata_path}")
            try:
                with open(self.metadata_path, "r") as f:
                    metadata = json.load(f)
                logger.info(f"Successfully loaded {len(metadata)} metadata entries")
                return metadata
            except Exception as e:
                logger.error(f"Failed to load metadata from {self.metadata_path}: {str(e)}")
                raise
        else:
            logger.info("No existing metadata file found, starting with empty metadata")
            return []

    def add(self, vectors: np.ndarray, metadatas: List[Dict]):
        if len(vectors) == 0:
            logger.warning("Attempted to add empty vector array, skipping")
            return

        logger.debug(f"Adding {len(vectors)} vectors to FAISS index")
        logger.debug(f"Vector shape: {vectors.shape}, expected dimension: {self.dim}")

        assert vectors.shape[1] == self.dim, f"Vector dimension mismatch: got {vectors.shape[1]}, expected {self.dim}"

        try:
            previous_count = self.index.ntotal
            self.index.add(vectors)
            self.metadata.extend(metadatas)
            logger.info(f"Added {len(vectors)} vectors to FAISS index (total: {previous_count} -> {self.index.ntotal})")
            
            self._persist()
        except Exception as e:
            logger.error(f"Failed to add vectors to FAISS index: {str(e)}")
            raise

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
                results.append(self.metadata[idx])

            logger.info(f"Search completed: found {len(results)} results out of {top_k} requested")
            return results
        except Exception as e:
            logger.error(f"Failed to search FAISS index: {str(e)}")
            raise

    def _persist(self):
        logger.debug(f"Persisting FAISS index to {self.index_path} and metadata to {self.metadata_path}")
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, "w") as f:
                json.dump(self.metadata, f, indent=2)
            logger.info(f"Successfully persisted FAISS index ({self.index.ntotal} vectors) and {len(self.metadata)} metadata entries")
        except Exception as e:
            logger.error(f"Failed to persist FAISS index or metadata: {str(e)}")
            raise
