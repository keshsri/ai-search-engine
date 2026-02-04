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
    # Amazon Nova doesn't require AWS Marketplace subscription (works with any payment method)
    # Nova Micro is the cheapest model on the market: $0.035/$0.14 per 1M tokens
    BEDROCK_MODEL_ID: str = "amazon.nova-micro-v1:0"  # Amazon Nova Micro (128K context, text-only)
    BEDROCK_MAX_TOKENS: int = 3000  # Nova Micro supports up to 5K output tokens
    BEDROCK_TEMPERATURE: float = 0.7

    # Tavily Web Search
    TAVILY_API_KEY: str = ""  # Set via environment variable or GitHub Secrets
    TAVILY_MAX_RESULTS: int = 3  # Number of web results to fetch
    TAVILY_SEARCH_DEPTH: str = "basic"  # "basic" or "advanced"

    class Config:
        env_file = ".env"


settings = Settings()
