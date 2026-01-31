import os
from pathlib import Path
from typing import BinaryIO
import shutil
import logging

logger = logging.getLogger(__name__)


class FileStorage:
    """
    Handles storage and retrieval of uploaded files.
    Currently stores locally, can be extended to use S3.
    """
    
    def __init__(self, storage_path: str = "uploads"):
        """
        Initialize file storage.
        
        Args:
            storage_path: Directory where files will be stored
        """
        self.storage_path = Path(storage_path)
        # Create uploads directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileStorage initialized with path: {self.storage_path.absolute()}")
    
    def save(self, file: BinaryIO, document_id: str, file_extension: str) -> str:
        """
        Save uploaded file to storage.
        
        Args:
            file: File object to save
            document_id: Unique document identifier
            file_extension: File extension (pdf, docx, txt)
        
        Returns:
            str: Path where file was saved
        """
        # Create filename: {document_id}.{extension}
        filename = f"{document_id}.{file_extension}"
        file_path = self.storage_path / filename
        
        logger.info(f"Saving file: {filename} to {file_path}")
        
        try:
            # Save file to disk
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file, f)
            
            file_size = file_path.stat().st_size
            logger.info(f"Successfully saved file: {filename} ({file_size} bytes)")
            
            return str(file_path)
        except Exception as e:
            logger.error(f"Failed to save file {filename}: {str(e)}")
            raise
    
    def get(self, document_id: str, file_extension: str) -> Path:
        """
        Get path to stored file.
        
        Args:
            document_id: Document identifier
            file_extension: File extension
        
        Returns:
            Path: Path to the file
        
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        filename = f"{document_id}.{file_extension}"
        file_path = self.storage_path / filename
        
        logger.debug(f"Retrieving file: {filename}")
        
        if not file_path.exists():
            logger.warning(f"File not found: {filename}")
            raise FileNotFoundError(f"File not found: {filename}")
        
        logger.debug(f"File found: {filename}")
        return file_path
    
    def delete(self, document_id: str, file_extension: str) -> bool:
        """
        Delete stored file.
        
        Args:
            document_id: Document identifier
            file_extension: File extension
        
        Returns:
            bool: True if deleted, False if file didn't exist
        """
        filename = f"{document_id}.{file_extension}"
        logger.info(f"Attempting to delete file: {filename}")
        
        try:
            file_path = self.get(document_id, file_extension)
            file_path.unlink()  # Delete file
            logger.info(f"Successfully deleted file: {filename}")
            return True
        except FileNotFoundError:
            logger.warning(f"Cannot delete - file not found: {filename}")
            return False
