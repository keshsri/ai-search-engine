import uuid
from typing import List
from app.models.chunk import Chunk

class ChunkingService:
    def __init__(self, chunk_size: int = 300, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, document_id: str, text: str) -> List[Chunk]:
        words = text.split()
        chunks = []
        start = 0
        index = 0

        while start < len(words):
            end = start + self.chunk_size
            content = " ".join(words[start:end])

            chunks.append(
                Chunk(
                    chunk_id = str(uuid.uuid4()),
                    document_id = document_id,
                    content = content,
                    index = index
                )
            )

            index += 1
            start = end - self.overlap

        return chunks