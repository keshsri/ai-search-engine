import uuid
from app.models.document import Document

class DocumentService:
    def ingest(self, document: Document) -> Document:
        document.id = str(uuid.uuid4())
        return document
