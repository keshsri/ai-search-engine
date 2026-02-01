from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Document(BaseModel):
    id: Optional[str] = None
    title: str
    content: str
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # File-related fields
    filename: Optional[str] = None  # Original filename (e.g., "report.pdf")
    file_type: Optional[str] = None  # File extension (pdf, docx, txt)
    file_size: Optional[int] = None  # Size in bytes
    file_path: Optional[str] = None  # Where file is stored


class DeleteDocumentRequest(BaseModel):
    """Request model for deleting a document."""
    document_id: str = Field(..., description="Document ID to delete")


class DeleteDocumentResponse(BaseModel):
    """Response model for document deletion."""
    document_id: str = Field(..., description="Deleted document ID")
    deleted: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Deletion status message")
