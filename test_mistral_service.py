import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import tempfile
import os
import json
from PIL import Image
import io

from mistral_service import MistralOCRService
from models import BillInfo, ProcessingStatus

class TestMistralOCRService:
    """Test cases for the Mistral OCR service"""
    
    def test_init_without_api_key(self):
        """Test initialization without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="MISTRAL_API_KEY environment variable is required"):
                MistralOCRService()
    
    @patch.dict(os.environ, {'MISTRAL_API_KEY': 'test_key'})
    def test_init_with_api_key(self):
        """Test successful initialization with API key"""
        with patch('mistral_service.Mistral') as mock_mistral:
            service = MistralOCRService()
            assert service.api_key == 'test_key'
            assert service.model == 'pixtral-12b-2409'
            mock_mistral.assert_called_once_with(api_key='test_key')
    
    @patch.dict(os.environ, {'MISTRAL_API_KEY': 'test_key'})
    @patch('mistral_service.Mistral')
    @pytest.mark.asyncio
    async def test_process_image_from_bytes_success(self, mock_mistral_class):
        """Test successful image processing"""
        # Setup mocks
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        
        # Mock the chat completion response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "restaurant_name": "Test Restaurant",
            "total": 25.50,
            "currency": "USD",
            "items": [
                {"name": "Burger", "price": 15.00, "quantity": 1},
                {"name": "Fries", "price": 5.50, "quantity": 1}
            ]
        })
        
        mock_client.chat.complete.return_value = mock_response
        
        # Create service and test image
        service = MistralOCRService()
        test_image_bytes = self._create_test_image_bytes()
        
        # Process the image
        result = await service.process_image_from_bytes(test_image_bytes, "test.jpg")
        
        # Verify results
        assert result["status"] == ProcessingStatus.SUCCESS
        assert result["message"] == "Bill processed successfully"
        assert result["bill_info"] is not None
        assert result["bill_info"].restaurant_name == "Test Restaurant"
        assert result["bill_info"].total == 25.50
        assert len(result["bill_info"].items) == 2
        assert result["raw_text"] is not None
    
    @patch.dict(os.environ, {'MISTRAL_API_KEY': 'test_key'})
    @patch('mistral_service.Mistral')
    @pytest.mark.asyncio
    async def test_process_image_from_bytes_api_error(self, mock_mistral_class):
        """Test image processing with API error"""
        # Setup mocks to raise an exception
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        mock_client.chat.complete.side_effect = Exception("API Error")
        
        # Create service and test image
        service = MistralOCRService()
        test_image_bytes = self._create_test_image_bytes()
        
        # Process the image
        result = await service.process_image_from_bytes(test_image_bytes, "test.jpg")
        
        # Verify error handling
        assert result["status"] == ProcessingStatus.ERROR
        assert "Failed to process image" in result["message"]
        assert result["bill_info"] is None
        assert result["raw_text"] is None
        assert "API Error" in result["error_details"]
    
    @patch.dict(os.environ, {'MISTRAL_API_KEY': 'test_key'})
    @patch('mistral_service.Mistral')
    def test_parse_bill_info_valid_json(self, mock_mistral_class):
        """Test parsing valid JSON response"""
        service = MistralOCRService()
        
        raw_text = '''
        Here is the extracted information:
        {
            "restaurant_name": "Pizza Palace",
            "date": "2024-01-15",
            "total": 32.75,
            "items": [
                {"name": "Margherita Pizza", "price": 18.00, "quantity": 1},
                {"name": "Coca Cola", "price": 3.50, "quantity": 2}
            ]
        }
        '''
        
        bill_info = service._parse_bill_info(raw_text)
        
        assert bill_info is not None
        assert bill_info.restaurant_name == "Pizza Palace"
        assert bill_info.date == "2024-01-15"
        assert bill_info.total == 32.75
        assert len(bill_info.items) == 2
        assert bill_info.items[0].name == "Margherita Pizza"
        assert bill_info.items[1].quantity == 2
    
    @patch.dict(os.environ, {'MISTRAL_API_KEY': 'test_key'})
    @patch('mistral_service.Mistral')
    def test_parse_bill_info_invalid_json(self, mock_mistral_class):
        """Test parsing invalid JSON response"""
        service = MistralOCRService()
        
        raw_text = "This is not valid JSON content"
        
        bill_info = service._parse_bill_info(raw_text)
        
        assert bill_info is not None
        assert bill_info.additional_info["raw_ocr_text"] == raw_text
    
    @patch.dict(os.environ, {'MISTRAL_API_KEY': 'test_key'})
    @patch('mistral_service.Mistral')
    def test_parse_bill_info_malformed_json(self, mock_mistral_class):
        """Test parsing malformed JSON response"""
        service = MistralOCRService()
        
        raw_text = '{"restaurant_name": "Test", "total": }'
        
        bill_info = service._parse_bill_info(raw_text)
        
        assert bill_info is not None
        assert bill_info.additional_info["raw_ocr_text"] == raw_text
        assert "parse_error" in bill_info.additional_info
    
    @patch.dict(os.environ, {'MISTRAL_API_KEY': 'test_key'})
    @patch('mistral_service.Mistral')
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.path.exists')
    @patch('os.unlink')
    @pytest.mark.asyncio
    async def test_temp_file_cleanup(self, mock_unlink, mock_exists, mock_temp_file, mock_mistral_class):
        """Test that temporary files are properly cleaned up"""
        # Setup mocks
        mock_temp = Mock()
        mock_temp.name = '/tmp/test_file.jpg'
        mock_temp.__enter__ = Mock(return_value=mock_temp)
        mock_temp.__exit__ = Mock(return_value=None)
        mock_temp_file.return_value = mock_temp
        mock_exists.return_value = True
        
        mock_client = Mock()
        mock_mistral_class.return_value = mock_client
        mock_client.chat.complete.side_effect = Exception("Test error")
        
        # Create service and test
        service = MistralOCRService()
        test_image_bytes = self._create_test_image_bytes()
        
        await service.process_image_from_bytes(test_image_bytes, "test.jpg")
        
        # Verify cleanup was called
        mock_unlink.assert_called_once_with('/tmp/test_file.jpg')
    
    def _create_test_image_bytes(self) -> bytes:
        """Create test image bytes for testing"""
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        return img_bytes.getvalue()

if __name__ == "__main__":
    pytest.main([__file__])