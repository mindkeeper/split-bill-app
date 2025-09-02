from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    """Status of bill processing"""
    SUCCESS = "success"
    ERROR = "error"
    PROCESSING = "processing"

class BillItem(BaseModel):
    """Individual item on a bill"""
    name: str = Field(..., description="Name of the item")
    price: float = Field(..., description="Price of the item")
    quantity: Optional[int] = Field(1, description="Quantity of the item")
    category: Optional[str] = Field(None, description="Category of the item")

class BillInfo(BaseModel):
    """Extracted bill information"""
    restaurant_name: Optional[str] = Field(None, description="Name of the restaurant/establishment")
    date: Optional[str] = Field(None, description="Date of the bill")
    time: Optional[str] = Field(None, description="Time of the bill")
    items: List[BillItem] = Field(default_factory=list, description="List of items on the bill")
    subtotal: Optional[float] = Field(None, description="Subtotal amount")
    tax: Optional[float] = Field(None, description="Tax amount")
    tip: Optional[float] = Field(None, description="Tip amount")
    total: Optional[float] = Field(None, description="Total amount")
    currency: Optional[str] = Field("USD", description="Currency of the bill")
    additional_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional extracted information")

class OCRResponse(BaseModel):
    """Response from OCR processing"""
    status: ProcessingStatus = Field(..., description="Processing status")
    message: str = Field(..., description="Processing message")
    bill_info: Optional[BillInfo] = Field(None, description="Extracted bill information")
    raw_text: Optional[str] = Field(None, description="Raw extracted text from OCR")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    error_details: Optional[str] = Field(None, description="Error details if processing failed")

class UploadResponse(BaseModel):
    """Response for file upload"""
    filename: str = Field(..., description="Name of the uploaded file")
    file_size: int = Field(..., description="Size of the uploaded file in bytes")
    content_type: str = Field(..., description="MIME type of the uploaded file")
    message: str = Field(..., description="Upload status message")

class MultipleBillsResponse(BaseModel):
    """Response for processing multiple bill images"""
    status: ProcessingStatus = Field(..., description="Overall processing status")
    message: str = Field(..., description="Overall processing message")
    total_images: int = Field(..., description="Total number of images processed")
    successful_images: int = Field(..., description="Number of successfully processed images")
    failed_images: int = Field(..., description="Number of failed image processing")
    bills: List[OCRResponse] = Field(default_factory=list, description="List of processed bill responses")
    total_processing_time: Optional[float] = Field(None, description="Total processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    errors: List[str] = Field(default_factory=list, description="List of error messages for failed images")