import uuid
from typing import Optional
from app.models.document import Document
from app.services.dynamodb_client import DynamoDBClient

class DocumentService:
    def __init__(self):
        self.db = DynamoDBClient()

    def ingest(self, document: Document) -> Document:
        document.id = document.id or str(uuid.uuid4())

        item = {
            "document_id": document.id,
            "title": document.title,
            "content": document.content,
            "source": document.source,
            "created_at": document.created_at.isoformat()
        }

        self.db.table.put_item(Item=item)
        return document

    def get_by_id(self, document_id: str) -> Optional[Document]:
        response = self.db.table.get_item(
            Key={"document_id": document_id}
        )

        item = response.get("Item")
        if not item:
            return None

        return Document(
            id = item["document_id"],
            title = item["title"],
            content = item["content"],
            source = item.get("source"),
            created_at = item["created_at"]
        )
