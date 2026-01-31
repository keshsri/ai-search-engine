import io
from typing import BinaryIO
import PyPDF2
from docx import Document as DocxDocument
import logging

logger = logging.getLogger(__name__)


class FileProcessor:
    """
    Extracts text content from various file formats.
    Supports: PDF, DOCX, TXT
    """
    
    SUPPORTED_TYPES = ["pdf", "docx", "txt"]
    
    def extract_text(self, file: BinaryIO, file_type: str) -> str:
        """
        Extract text from uploaded file.
        
        Args:
            file: File object
            file_type: Type of file (pdf, docx, txt)
        
        Returns:
            str: Extracted text content
        
        Raises:
            ValueError: If file type is not supported
        """
        file_type = file_type.lower()
        
        logger.info(f"Starting text extraction for file type: {file_type}")
        
        if file_type not in self.SUPPORTED_TYPES:
            logger.error(f"Unsupported file type: {file_type}")
            raise ValueError(f"Unsupported file type: {file_type}. Supported: {self.SUPPORTED_TYPES}")
        
        # Extract based on file type
        if file_type == "pdf":
            return self._extract_from_pdf(file)
        elif file_type == "docx":
            return self._extract_from_docx(file)
        elif file_type == "txt":
            return self._extract_from_txt(file)
    
    def _extract_from_pdf(self, file: BinaryIO) -> str:
        """
        Extract text from PDF file.
        
        Args:
            file: PDF file object
        
        Returns:
            str: Extracted text
        """
        logger.debug("Extracting text from PDF")
        
        try:
            # Create PDF reader
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            logger.info(f"PDF has {num_pages} pages")
            
            # Extract text from all pages
            text_parts = []
            for i, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text:
                    text_parts.append(text)
                    logger.debug(f"Extracted text from page {i}/{num_pages} ({len(text)} chars)")
            
            # Combine all pages
            full_text = "\n\n".join(text_parts)
            logger.info(f"Successfully extracted {len(full_text)} characters from PDF")
            
            return self._clean_text(full_text)
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise ValueError(f"Error extracting text from PDF: {str(e)}")
    
    def _extract_from_docx(self, file: BinaryIO) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            file: DOCX file object
        
        Returns:
            str: Extracted text
        """
        logger.debug("Extracting text from DOCX")
        
        try:
            # Load document
            doc = DocxDocument(file)
            num_paragraphs = len(doc.paragraphs)
            logger.info(f"DOCX has {num_paragraphs} paragraphs")
            
            # Extract text from all paragraphs
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            # Combine all paragraphs
            full_text = "\n\n".join(text_parts)
            logger.info(f"Successfully extracted {len(full_text)} characters from DOCX")
            
            return self._clean_text(full_text)
        
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            raise ValueError(f"Error extracting text from DOCX: {str(e)}")
    
    def _extract_from_txt(self, file: BinaryIO) -> str:
        """
        Extract text from TXT file.
        
        Args:
            file: TXT file object
        
        Returns:
            str: Extracted text
        """
        logger.debug("Extracting text from TXT")
        
        try:
            # Read and decode text
            content = file.read()
            
            # Try UTF-8 first, fallback to latin-1
            try:
                text = content.decode('utf-8')
                logger.debug("Decoded TXT file as UTF-8")
            except UnicodeDecodeError:
                text = content.decode('latin-1')
                logger.debug("Decoded TXT file as latin-1 (UTF-8 failed)")
            
            logger.info(f"Successfully extracted {len(text)} characters from TXT")
            
            return self._clean_text(text)
        
        except Exception as e:
            logger.error(f"Error extracting text from TXT: {str(e)}")
            raise ValueError(f"Error extracting text from TXT: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.
        
        Args:
            text: Raw extracted text
        
        Returns:
            str: Cleaned text
        """
        logger.debug(f"Cleaning text ({len(text)} chars before cleaning)")
        
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]  # Remove empty lines
        
        # Join with single newline
        cleaned = '\n'.join(lines)
        
        logger.debug(f"Text cleaned ({len(cleaned)} chars after cleaning)")
        
        return cleaned
