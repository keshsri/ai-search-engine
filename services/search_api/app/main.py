from fastapi import FastAPI
from app.api import health, documents, search
from app.core.logging import setup_logging
from app.core.config import settings

# Setup logging
setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered semantic search engine using RAG",
    version="0.1.0"
)

# ---- Routers ----
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(search.router)
