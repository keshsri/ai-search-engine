from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ai-search-engine"
    ENV: str = "dev"

    # AWS
    AWS_REGION: str = "us-east-1"
    DYNAMODB_DOCUMENT_TABLE: str = "ai-search-documents"
    CHUNKS_TABLE_NAME: str = "document_chunks"
    CONVERSATIONS_TABLE_NAME: str = "conversations"

    # Chunking
    CHUNK_SIZE: int = 300

    # Embeddings
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_PROVIDER: str = "dummy"  # dummy | bedrock

    # FAISS
    FAISS_TOP_K: int = 5

    # Bedrock / LLM
    # Amazon Titan doesn't require AWS Marketplace subscription (works with any payment method)
    # Claude models require US payment method for Marketplace subscription
    BEDROCK_MODEL_ID: str = "amazon.titan-text-premier-v1:0"  # Amazon Titan Text Premier (32K context)
    BEDROCK_MAX_TOKENS: int = 3000  # Premier supports up to 32K tokens
    BEDROCK_TEMPERATURE: float = 0.7

    class Config:
        env_file = ".env"


settings = Settings()
