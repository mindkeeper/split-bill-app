"""Custom exceptions for the application"""

from fastapi import HTTPException, status
from typing import Optional, Dict, Any

class SplitBillException(HTTPException):
    """Base exception for Split Bill application"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class FileValidationError(SplitBillException):
    """Exception raised when file validation fails"""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File validation error: {detail}"
        )

class OCRProcessingError(SplitBillException):
    """Exception raised when OCR processing fails"""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR processing error: {detail}"
        )

class ServiceUnavailableError(SplitBillException):
    """Exception raised when external service is unavailable"""
    
    def __init__(self, service_name: str, detail: Optional[str] = None):
        message = f"{service_name} service is currently unavailable"
        if detail:
            message += f": {detail}"
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=message
        )

class InvalidFileTypeError(FileValidationError):
    """Exception raised when file type is not supported"""
    
    def __init__(self, file_type: str, allowed_types: list):
        super().__init__(
            f"File type '{file_type}' is not supported. Allowed types: {', '.join(allowed_types)}"
        )

class FileSizeError(FileValidationError):
    """Exception raised when file size exceeds limit"""
    
    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            f"File size {file_size} bytes exceeds maximum allowed size of {max_size} bytes"
        )

class APIKeyError(ServiceUnavailableError):
    """Exception raised when API key is missing or invalid"""
    
    def __init__(self, service_name: str):
        super().__init__(
            service_name,
            "API key is not properly configured"
        )

class RateLimitError(SplitBillException):
    """Exception raised when API rate limit is exceeded"""
    
    def __init__(self, service_name: str, retry_after: Optional[int] = None):
        message = f"{service_name} rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=message,
            headers={"Retry-After": str(retry_after)} if retry_after else None
        )

class AuthenticationError(SplitBillException):
    """Exception raised when authentication fails"""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )

class AuthorizationError(SplitBillException):
    """Exception raised when authorization fails"""
    
    def __init__(self, detail: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class ResourceNotFoundError(SplitBillException):
    """Exception raised when a requested resource is not found"""
    
    def __init__(self, resource_type: str, resource_id: str = None):
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )

class ConflictError(SplitBillException):
    """Exception raised when there's a conflict with the current state"""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )

class BadRequestError(SplitBillException):
    """Exception raised for malformed requests"""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )