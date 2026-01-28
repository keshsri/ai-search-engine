from fastapi import FastAPI
from app.api import health, documents

app = FastAPI(title="AI Search Engine")

app.include_router(health.router)
app.include_router(documents.router)