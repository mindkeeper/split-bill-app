"""Response utilities for standardized API responses"""

from typing import Optional, Any, Dict
from datetime import datetime
import uuid
from app.models.responses import (
    BaseResponse,
    ErrorResponse,
    OCRResponse,
    OCRResultData,
    UploadResponse,
    UploadResultData,
    MultipleBillsResponse,
    MultipleBillsResultData,
    HealthResponse
)
from app.models.schemas import BillInfo

def generate_request_id() -> str:
    """Generate a unique request ID"""
    return str(uuid.uuid4())

def create_success_response(
    message: str,
    data: Optional[Any] = None,
    request_id: Optional[str] = None
) -> BaseResponse:
    """Create a standardized success response"""
    return BaseResponse(
        success=True,
        message=message,
        data=data,
        request_id=request_id or generate_request_id()
    )

def create_error_response(
    message: str,
    error_code: Optional[str] = None,
    error_details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """Create a standardized error response"""
    return ErrorResponse(
        message=message,
        error_code=error_code,
        error_details=error_details,
        request_id=request_id or generate_request_id()
    )

def create_ocr_response(
    message: str,
    bill_info: Optional[BillInfo] = None,
    raw_text: Optional[str] = None,
    processing_time: Optional[float] = None,
    confidence_score: Optional[float] = None,
    request_id: Optional[str] = None
) -> OCRResponse:
    """Create a standardized OCR response"""
    data = OCRResultData(
        bill_info=bill_info,
        raw_text=raw_text,
        processing_time=processing_time,
        confidence_score=confidence_score
    )
    
    return OCRResponse(
        success=True,
        message=message,
        data=data,
        request_id=request_id or generate_request_id()
    )

def create_upload_response(
    message: str,
    filename: str,
    file_size: int,
    content_type: str,
    file_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> UploadResponse:
    """Create a standardized upload response"""
    data = UploadResultData(
        filename=filename,
        file_size=file_size,
        content_type=content_type,
        file_id=file_id
    )
    
    return UploadResponse(
        success=True,
        message=message,
        data=data,
        request_id=request_id or generate_request_id()
    )

def create_multiple_bills_response(
    message: str,
    total_images: int,
    successful_images: int,
    failed_images: int,
    bills: list,
    total_processing_time: Optional[float] = None,
    errors: Optional[list] = None,
    request_id: Optional[str] = None
) -> MultipleBillsResponse:
    """Create a standardized multiple bills response"""
    data = MultipleBillsResultData(
        total_images=total_images,
        successful_images=successful_images,
        failed_images=failed_images,
        bills=bills,
        total_processing_time=total_processing_time,
        errors=errors or []
    )
    
    return MultipleBillsResponse(
        success=True,
        message=message,
        data=data,
        request_id=request_id or generate_request_id()
    )

def create_health_response(
    status: str,
    message: str,
    version: str,
    services: Optional[Dict[str, str]] = None
) -> HealthResponse:
    """Create a standardized health response"""
    return HealthResponse(
        status=status,
        message=message,
        version=version,
        services=services
    )