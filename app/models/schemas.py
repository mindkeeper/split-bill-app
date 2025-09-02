from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import re

class ProcessingStatus(str, Enum):
    """Status of bill processing"""
    SUCCESS = "success"
    ERROR = "error"
    PROCESSING = "processing"

class BillItem(BaseModel):
    """Individual item on a bill"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    name: str = Field(..., min_length=1, max_length=200, description="Name of the item")
    price: float = Field(..., gt=0, description="Price of the item (must be positive)")
    quantity: Optional[int] = Field(1, ge=1, le=1000, description="Quantity of the item")
    category: Optional[str] = Field(None, max_length=100, description="Category of the item")
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        # Round to 2 decimal places for currency
        return round(v, 2)

class BillInfo(BaseModel):
    """Extracted bill information"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    restaurant_name: Optional[str] = Field(None, max_length=200, description="Name of the restaurant/establishment")
    date: Optional[str] = Field(None, description="Date of the bill")
    time: Optional[str] = Field(None, description="Time of the bill")
    items: List[BillItem] = Field(default_factory=list, max_items=100, description="List of items on the bill")
    subtotal: Optional[float] = Field(None, ge=0, description="Subtotal amount")
    tax: Optional[float] = Field(None, ge=0, description="Tax amount")
    tip: Optional[float] = Field(None, ge=0, description="Tip amount")
    total: Optional[float] = Field(None, ge=0, description="Total amount")
    currency: Optional[str] = Field("USD", min_length=3, max_length=3, description="Currency of the bill (ISO 4217 code)")
    additional_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional extracted information")
    
    @validator('currency')
    def validate_currency(cls, v):
        if v is None:
            return v
        # Common currency codes validation
        valid_currencies = {'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'SEK', 'NZD'}
        v_upper = v.upper()
        if v_upper not in valid_currencies:
            raise ValueError(f'Currency must be a valid ISO 4217 code. Supported: {", ".join(valid_currencies)}')
        return v_upper
    
    @validator('subtotal', 'tax', 'tip', 'total')
    def validate_amounts(cls, v):
        if v is not None and v < 0:
            raise ValueError('Financial amounts must be non-negative')
        if v is not None:
            return round(v, 2)
        return v
    
    @validator('date')
    def validate_date_format(cls, v):
        if v is None:
            return v
        # Accept various date formats
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            r'\d{1,2}/\d{1,2}/\d{4}',  # M/D/YYYY
        ]
        if not any(re.match(pattern, v.strip()) for pattern in date_patterns):
            # Don't raise error, just return as-is for flexibility
            pass
        return v.strip()
    
    @validator('time')
    def validate_time_format(cls, v):
        if v is None:
            return v
        # Accept various time formats
        time_patterns = [
            r'\d{1,2}:\d{2}',  # H:MM or HH:MM
            r'\d{1,2}:\d{2}:\d{2}',  # H:MM:SS or HH:MM:SS
            r'\d{1,2}:\d{2}\s?(AM|PM|am|pm)',  # H:MM AM/PM
        ]
        if not any(re.match(pattern, v.strip()) for pattern in time_patterns):
            # Don't raise error, just return as-is for flexibility
            pass
        return v.strip()

# Response models have been moved to app.models.responses for better organization
# This file now contains only core data schemas
