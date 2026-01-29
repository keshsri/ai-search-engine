from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ai-search-engine"
    ENV: str = "dev"

    # AWS
    AWS_REGION: str = "us-east-1"
    DYNAMODB_DOCUMENT_TABLE: str = "ai-search-documents"

    # Chunking
    CHUNK_SIZE: int = 300

    # Embeddings
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_PROVIDER: str = "dummy"  # dummy | bedrock

    # FAISS
    FAISS_TOP_K: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
