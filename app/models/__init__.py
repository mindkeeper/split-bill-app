"""Data models for the Split Bill application"""

from .schemas import (
    ProcessingStatus,
    BillItem,
    BillInfo
)

from .responses import (
    BaseResponse,
    ErrorResponse,
    HealthResponse,
    OCRResponse,
    OCRResultData,
    UploadResponse,
    UploadResultData,
    MultipleBillsResponse,
    MultipleBillsResultData,
    ValidationErrorResponse,
    ValidationErrorDetail
)

__all__ = [
    # Core data models
    "ProcessingStatus",
    "BillItem",
    "BillInfo",
    
    # Standardized response models
    "BaseResponse",
    "ErrorResponse",
    "HealthResponse",
    "OCRResponse",
    "OCRResultData",
    "UploadResponse",
    "UploadResultData",
    "MultipleBillsResponse",
    "MultipleBillsResultData",
    "ValidationErrorResponse",
    "ValidationErrorDetail"
]