from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Chunk(BaseModel):
    chunk_id: Optional[str]
    document_id: str
    content: str
    index: int
    created_at: datetime = Field(default_factory=datetime.utcnow)