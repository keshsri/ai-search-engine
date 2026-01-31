import os
from pathlib import Path
from typing import BinaryIO
import shutil
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class FileStorage:
    """
    Handles storage and retrieval of uploaded files.
    In Lambda, uses S3 for persistent storage.
    Locally, uses local file system.
    """
    
    def __init__(self, storage_path: str = None):
        """
        Initialize file storage.
        
        Args:
            storage_path: Directory where files will be stored locally.
                         Defaults to /tmp/uploads in Lambda, uploads/ locally.
        """
        # Detect Lambda environment
        self.use_s3 = os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None
        
        if self.use_s3:
            # S3 configuration
            self.s3_client = boto3.client('s3')
            self.s3_bucket = os.environ.get('DOCUMENTS_BUCKET')
            self.s3_prefix = 'documents/'
            # Still use /tmp for temporary file operations
            storage_path = "/tmp/uploads"
            logger.info(f"Running in Lambda, using S3 bucket: {self.s3_bucket}")
        else:
            # Local file storage
            if storage_path is None:
                storage_path = "uploads"
            logger.info("Running locally, using local file storage")
        
        self.storage_path = Path(storage_path)
        # Create uploads directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileStorage initialized with path: {self.storage_path.absolute()}")
    
    def save(self, file: BinaryIO, document_id: str, file_extension: str) -> str:
        """
        Save uploaded file to storage (S3 in Lambda, local otherwise).
        
        Args:
            file: File object to save
            document_id: Unique document identifier
            file_extension: File extension (pdf, docx, txt)
        
        Returns:
            str: S3 key (if Lambda) or local path (if local)
        """
        filename = f"{document_id}.{file_extension}"
        file_path = self.storage_path / filename
        
        logger.info(f"Saving file: {filename}")
        
        try:
            # Save to local /tmp first
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file, f)
            
            file_size = file_path.stat().st_size
            logger.info(f"Saved file locally: {filename} ({file_size} bytes)")
            
            # Upload to S3 if in Lambda
            if self.use_s3:
                s3_key = f"{self.s3_prefix}{filename}"
                logger.info(f"Uploading {filename} to S3: {self.s3_bucket}/{s3_key}")
                self.s3_client.upload_file(str(file_path), self.s3_bucket, s3_key)
                logger.info(f"Successfully uploaded {filename} to S3")
                return s3_key
            else:
                return str(file_path)
        except Exception as e:
            logger.error(f"Failed to save file {filename}: {str(e)}")
            raise
    
    def get(self, document_id: str, file_extension: str) -> Path:
        """
        Get path to stored file (downloads from S3 if needed).
        
        Args:
            document_id: Document identifier
            file_extension: File extension
        
        Returns:
            Path: Local path to the file
        
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        filename = f"{document_id}.{file_extension}"
        file_path = self.storage_path / filename
        
        logger.debug(f"Retrieving file: {filename}")
        
        # If using S3, download file if not in local cache
        if self.use_s3 and not file_path.exists():
            s3_key = f"{self.s3_prefix}{filename}"
            try:
                logger.info(f"Downloading {filename} from S3: {self.s3_bucket}/{s3_key}")
                self.s3_client.download_file(self.s3_bucket, s3_key, str(file_path))
                logger.info(f"Successfully downloaded {filename} from S3")
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    logger.warning(f"File not found in S3: {s3_key}")
                    raise FileNotFoundError(f"File not found: {filename}")
                else:
                    logger.error(f"Failed to download {filename} from S3: {str(e)}")
                    raise
        
        if not file_path.exists():
            logger.warning(f"File not found: {filename}")
            raise FileNotFoundError(f"File not found: {filename}")
        
        logger.debug(f"File found: {filename}")
        return file_path
    
    def delete(self, document_id: str, file_extension: str) -> bool:
        """
        Delete stored file (from S3 and local cache).
        
        Args:
            document_id: Document identifier
            file_extension: File extension
        
        Returns:
            bool: True if deleted, False if file didn't exist
        """
        filename = f"{document_id}.{file_extension}"
        logger.info(f"Attempting to delete file: {filename}")
        
        deleted = False
        
        # Delete from S3 if in Lambda
        if self.use_s3:
            s3_key = f"{self.s3_prefix}{filename}"
            try:
                logger.info(f"Deleting {filename} from S3: {self.s3_bucket}/{s3_key}")
                self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
                logger.info(f"Successfully deleted {filename} from S3")
                deleted = True
            except Exception as e:
                logger.error(f"Failed to delete {filename} from S3: {str(e)}")
        
        # Delete local file
        try:
            file_path = self.storage_path / filename
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Successfully deleted local file: {filename}")
                deleted = True
        except Exception as e:
            logger.warning(f"Failed to delete local file {filename}: {str(e)}")
        
        if not deleted:
            logger.warning(f"File not found for deletion: {filename}")
        
        return deleted
