from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Document(BaseModel):
    id: Optional[str] = None
    title: str
    content: str
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
