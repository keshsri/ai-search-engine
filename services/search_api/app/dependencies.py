from app.vector_store.faiss_vector_store import FAISSVectorStore
from app.core.config import settings

_vector_store = None  # module-level singleton

def get_vector_store() -> FAISSVectorStore:
    global _vector_store

    if _vector_store is None:
        _vector_store = FAISSVectorStore(
            dim=settings.EMBEDDING_DIMENSION
        )

    return _vector_store
