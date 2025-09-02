"""File validation utilities"""

from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import InvalidFileTypeError, FileSizeError
import logging

logger = logging.getLogger(__name__)

def validate_image_file(file: UploadFile) -> bool:
    """Validate uploaded image file
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        bool: True if file is valid
        
    Raises:
        InvalidFileTypeError: If file type is not supported
        FileSizeError: If file size exceeds limit
    """
    # Check file type
    if file.content_type not in settings.allowed_file_types_list:
        logger.warning(f"Invalid file type: {file.content_type}")
        raise InvalidFileTypeError(file.content_type, settings.allowed_file_types_list)
    
    # Check file size (if available)
    if hasattr(file, 'size') and file.size:
        if file.size > settings.max_file_size:
            logger.warning(f"File size {file.size} exceeds limit {settings.max_file_size}")
            raise FileSizeError(file.size, settings.max_file_size)
    
    logger.info(f"File validation passed: {file.filename} ({file.content_type})")
    return True

def get_file_info(file: UploadFile) -> dict:
    """Get file information
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        dict: File information
    """
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": getattr(file, 'size', None)
    }