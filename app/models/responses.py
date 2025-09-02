"""Standardized response models for API endpoints"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime
from .schemas import ProcessingStatus, BillInfo

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    """Base response model for all API responses"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., min_length=1, max_length=500, description="Response message")
    data: Optional[T] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    request_id: Optional[str] = Field(None, max_length=100, description="Unique request identifier")
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

class ErrorResponse(BaseModel):
    """Error response model"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    success: bool = Field(False, description="Always false for error responses")
    message: str = Field(..., min_length=1, max_length=500, description="Error message")
    error_code: Optional[str] = Field(None, max_length=50, description="Specific error code")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, max_length=100, description="Unique request identifier")
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Error message cannot be empty')
        return v.strip()
    
    @validator('error_code')
    def validate_error_code(cls, v):
        if v is not None:
            # Ensure error codes follow a standard format (uppercase, alphanumeric with underscores)
            import re
            if not re.match(r'^[A-Z0-9_]+$', v):
                raise ValueError('Error code must be uppercase alphanumeric with underscores')
        return v

class HealthResponse(BaseModel):
    """Health check response"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    status: str = Field(..., description="Service health status")
    message: str = Field(..., min_length=1, max_length=200, description="Health check message")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    services: Optional[Dict[str, str]] = Field(None, description="Status of dependent services")
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = {'healthy', 'degraded', 'unhealthy'}
        if v.lower() not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v.lower()
    
    @validator('version')
    def validate_version(cls, v):
        import re
        # Validate semantic versioning format (e.g., 1.0.0, 1.2.3-beta)
        if not re.match(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$', v):
            raise ValueError('Version must follow semantic versioning format (e.g., 1.0.0)')
        return v

class OCRResultData(BaseModel):
    """OCR processing result data"""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    bill_info: Optional[BillInfo] = Field(None, description="Extracted bill information")
    raw_text: Optional[str] = Field(None, max_length=10000, description="Raw extracted text from OCR")
    processing_time: Optional[float] = Field(None, ge=0, le=300, description="Processing time in seconds")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="OCR confidence score (0-1)")
    
    @validator('processing_time')
    def validate_processing_time(cls, v):
        if v is not None and v < 0:
            raise ValueError('Processing time must be non-negative')
        if v is not None:
            return round(v, 3)  # Round to milliseconds
        return v
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Confidence score must be between 0 and 1')
        if v is not None:
            return round(v, 3)
        return v

class OCRResponse(BaseResponse[OCRResultData]):
    """Response for single bill OCR processing"""
    pass

class UploadResultData(BaseModel):
    """File upload result data"""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    filename: str = Field(..., min_length=1, max_length=255, description="Name of the uploaded file")
    file_size: int = Field(..., gt=0, le=50*1024*1024, description="Size of the uploaded file in bytes (max 50MB)")
    content_type: str = Field(..., description="MIME type of the uploaded file")
    file_id: Optional[str] = Field(None, max_length=100, description="Unique file identifier")
    
    @validator('filename')
    def validate_filename(cls, v):
        import re
        # Remove any path separators for security
        v = v.replace('/', '').replace('\\', '')
        # Ensure filename has valid characters
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError('Filename contains invalid characters')
        return v
    
    @validator('content_type')
    def validate_content_type(cls, v):
        # Validate common image MIME types
        valid_types = {
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
            'image/bmp', 'image/webp', 'image/tiff', 'application/pdf'
        }
        if v.lower() not in valid_types:
            raise ValueError(f'Content type must be one of: {", ".join(valid_types)}')
        return v.lower()

class UploadResponse(BaseResponse[UploadResultData]):
    """Response for file upload"""
    pass

class MultipleBillsResultData(BaseModel):
    """Multiple bills processing result data"""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    total_images: int = Field(..., ge=0, le=100, description="Total number of images processed")
    successful_images: int = Field(..., ge=0, description="Number of successfully processed images")
    failed_images: int = Field(..., ge=0, description="Number of failed image processing")
    bills: List[OCRResultData] = Field(default_factory=list, max_items=100, description="List of processed bill results")
    total_processing_time: Optional[float] = Field(None, ge=0, description="Total processing time in seconds")
    errors: List[str] = Field(default_factory=list, max_items=100, description="List of error messages for failed images")
    
    @validator('successful_images', 'failed_images')
    def validate_image_counts(cls, v, values):
        if 'total_images' in values and v > values['total_images']:
            raise ValueError('Image count cannot exceed total images')
        return v
    
    @validator('total_processing_time')
    def validate_total_processing_time(cls, v):
        if v is not None and v < 0:
            raise ValueError('Total processing time must be non-negative')
        if v is not None:
            return round(v, 3)
        return v
    
    @validator('errors')
    def validate_errors(cls, v):
        # Ensure error messages are not empty and have reasonable length
        validated_errors = []
        for error in v:
            if error and error.strip() and len(error.strip()) <= 500:
                validated_errors.append(error.strip())
        return validated_errors

class MultipleBillsResponse(BaseResponse[MultipleBillsResultData]):
    """Response for processing multiple bill images"""
    pass

class ValidationErrorDetail(BaseModel):
    """Validation error detail"""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    field: str = Field(..., min_length=1, max_length=100, description="Field that failed validation")
    message: str = Field(..., min_length=1, max_length=300, description="Validation error message")
    value: Optional[Any] = Field(None, description="Invalid value")
    
    @validator('field')
    def validate_field(cls, v):
        import re
        # Ensure field name follows standard naming conventions
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_.]*$', v):
            raise ValueError('Field name must be a valid identifier')
        return v
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Validation error message cannot be empty')
        return v.strip()

class ValidationErrorResponse(ErrorResponse):
    """Validation error response"""
    validation_errors: List[ValidationErrorDetail] = Field(
        default_factory=list,
        description="List of validation errors"
    )