#!/usr/bin/env python3
"""Test suite for response model validation and serialization"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.responses import (
    BaseResponse, ErrorResponse, HealthResponse, OCRResultData,
    UploadResultData, MultipleBillsResultData, ValidationErrorDetail
)
from app.models.schemas import BillItem, BillInfo, ProcessingStatus


class TestBillItemValidation:
    """Test BillItem model validation"""
    
    def test_valid_bill_item(self):
        """Test creating a valid bill item"""
        item = BillItem(
            name="Coffee",
            price=4.50,
            quantity=2,
            category="Beverages"
        )
        assert item.name == "Coffee"
        assert item.price == 4.50
        assert item.quantity == 2
        assert item.category == "Beverages"
    
    def test_price_validation(self):
        """Test price validation constraints"""
        # Test negative price
        with pytest.raises(ValidationError):
            BillItem(name="Coffee", price=-1.0)
        
        # Test zero price
        with pytest.raises(ValidationError):
            BillItem(name="Coffee", price=0)
        
        # Test price rounding
        item = BillItem(name="Coffee", price=4.567)
        assert item.price == 4.57
    
    def test_name_validation(self):
        """Test name validation constraints"""
        # Test empty name
        with pytest.raises(ValidationError):
            BillItem(name="", price=1.0)
        
        # Test name too long
        with pytest.raises(ValidationError):
            BillItem(name="x" * 201, price=1.0)
    
    def test_quantity_validation(self):
        """Test quantity validation constraints"""
        # Test negative quantity
        with pytest.raises(ValidationError):
            BillItem(name="Coffee", price=1.0, quantity=-1)
        
        # Test zero quantity
        with pytest.raises(ValidationError):
            BillItem(name="Coffee", price=1.0, quantity=0)
        
        # Test quantity too large
        with pytest.raises(ValidationError):
            BillItem(name="Coffee", price=1.0, quantity=1001)


class TestBillInfoValidation:
    """Test BillInfo model validation"""
    
    def test_valid_bill_info(self):
        """Test creating valid bill info"""
        bill = BillInfo(
            restaurant_name="Test Restaurant",
            date="2024-01-15",
            time="12:30",
            currency="USD",
            total=25.50
        )
        assert bill.restaurant_name == "Test Restaurant"
        assert bill.currency == "USD"
        assert bill.total == 25.50
    
    def test_currency_validation(self):
        """Test currency validation"""
        # Test valid currency
        bill = BillInfo(currency="usd")
        assert bill.currency == "USD"
        
        # Test invalid currency
        with pytest.raises(ValidationError):
            BillInfo(currency="INVALID")
    
    def test_amount_validation(self):
        """Test financial amount validation"""
        # Test negative amounts
        with pytest.raises(ValidationError):
            BillInfo(total=-10.0)
        
        with pytest.raises(ValidationError):
            BillInfo(tax=-5.0)
        
        # Test amount rounding
        bill = BillInfo(total=25.567)
        assert bill.total == 25.57
    
    def test_items_limit(self):
        """Test items list size limit"""
        items = [BillItem(name=f"Item {i}", price=1.0) for i in range(101)]
        with pytest.raises(ValidationError):
            BillInfo(items=items)


class TestResponseValidation:
    """Test response model validation"""
    
    def test_base_response_validation(self):
        """Test BaseResponse validation"""
        # Test valid response
        response = BaseResponse[str](
            success=True,
            message="Success",
            data="test data"
        )
        assert response.success is True
        assert response.message == "Success"
        assert response.data == "test data"
        
        # Test empty message
        with pytest.raises(ValidationError):
            BaseResponse[str](success=True, message="")
        
        # Test message too long
        with pytest.raises(ValidationError):
            BaseResponse[str](success=True, message="x" * 501)
    
    def test_error_response_validation(self):
        """Test ErrorResponse validation"""
        # Test valid error response
        error = ErrorResponse(
            message="Test error",
            error_code="TEST_ERROR"
        )
        assert error.success is False
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        
        # Test invalid error code format
        with pytest.raises(ValidationError):
            ErrorResponse(message="Test", error_code="invalid-code")
    
    def test_health_response_validation(self):
        """Test HealthResponse validation"""
        # Test valid health response
        health = HealthResponse(
            status="healthy",
            message="All systems operational",
            version="1.0.0"
        )
        assert health.status == "healthy"
        assert health.version == "1.0.0"
        
        # Test invalid status
        with pytest.raises(ValidationError):
            HealthResponse(
                status="invalid",
                message="Test",
                version="1.0.0"
            )
        
        # Test invalid version format
        with pytest.raises(ValidationError):
            HealthResponse(
                status="healthy",
                message="Test",
                version="invalid-version"
            )
    
    def test_ocr_result_data_validation(self):
        """Test OCRResultData validation"""
        # Test valid OCR result
        ocr_data = OCRResultData(
            raw_text="Sample text",
            processing_time=1.234,
            confidence_score=0.95
        )
        assert ocr_data.processing_time == 1.234
        assert ocr_data.confidence_score == 0.95
        
        # Test invalid confidence score
        with pytest.raises(ValidationError):
            OCRResultData(confidence_score=1.5)
        
        # Test negative processing time
        with pytest.raises(ValidationError):
            OCRResultData(processing_time=-1.0)
    
    def test_upload_result_data_validation(self):
        """Test UploadResultData validation"""
        # Test valid upload result
        upload_data = UploadResultData(
            filename="test.jpg",
            file_size=1024,
            content_type="image/jpeg"
        )
        assert upload_data.filename == "test.jpg"
        assert upload_data.content_type == "image/jpeg"
        
        # Test invalid filename with special characters
        with pytest.raises(ValidationError):
            UploadResultData(
                filename="test@#$.jpg",
                file_size=1024,
                content_type="image/jpeg"
            )
        
        # Test invalid content type
        with pytest.raises(ValidationError):
            UploadResultData(
                filename="test.txt",
                file_size=1024,
                content_type="text/plain"
            )
        
        # Test file size too large
        with pytest.raises(ValidationError):
            UploadResultData(
                filename="test.jpg",
                file_size=60 * 1024 * 1024,  # 60MB
                content_type="image/jpeg"
            )
    
    def test_validation_error_detail(self):
        """Test ValidationErrorDetail validation"""
        # Test valid validation error
        error_detail = ValidationErrorDetail(
            field="email",
            message="Invalid email format",
            value="invalid-email"
        )
        assert error_detail.field == "email"
        assert error_detail.message == "Invalid email format"
        
        # Test invalid field name
        with pytest.raises(ValidationError):
            ValidationErrorDetail(
                field="123invalid",
                message="Test message"
            )


class TestSerializationBestPractices:
    """Test serialization best practices"""
    
    def test_datetime_serialization(self):
        """Test datetime serialization to ISO format"""
        response = BaseResponse[str](
            success=True,
            message="Test",
            data="test"
        )
        
        # Test model_dump with json mode
        serialized = response.model_dump(mode='json')
        assert isinstance(serialized['timestamp'], str)
        assert 'T' in serialized['timestamp']  # ISO format indicator
    
    def test_whitespace_stripping(self):
        """Test automatic whitespace stripping"""
        response = BaseResponse[str](
            success=True,
            message="  Test Message  ",
            data="test"
        )
        assert response.message == "Test Message"
    
    def test_assignment_validation(self):
        """Test validation on assignment"""
        response = BaseResponse[str](
            success=True,
            message="Test",
            data="test"
        )
        
        # Test that assignment validation works
        with pytest.raises(ValidationError):
            response.message = ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])