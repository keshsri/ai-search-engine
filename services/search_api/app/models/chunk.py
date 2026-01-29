from pydantic import BaseModel
from typing import Optional

class Chunk(BaseModel):
    chunk_id: Optional[str]
    document_id: str
    content: str
    index: int