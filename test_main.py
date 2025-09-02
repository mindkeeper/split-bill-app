import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import io
from PIL import Image
import os

# Import the FastAPI app
from main import app
from models import ProcessingStatus, BillInfo

# Create test client
client = TestClient(app)

class TestAPI:
    """Test cases for the main API endpoints"""
    
    def test_health_check(self):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "Split Bill Backend API" in data["message"]
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Welcome to Split Bill Backend API"
        assert data["version"] == "1.0.0"
        assert "/process-bill" in data["endpoints"]
    
    def test_upload_test_endpoint(self):
        """Test the file upload test endpoint"""
        # Create a test image
        test_image = self._create_test_image()
        
        response = client.post(
            "/upload-test",
            files={"file": ("test.jpg", test_image, "image/jpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.jpg"
        assert data["content_type"] == "image/jpeg"
        assert data["message"] == "File uploaded successfully"
        assert data["file_size"] > 0
    
    def test_process_bill_invalid_file_type(self):
        """Test processing with invalid file type"""
        # Create a text file instead of image
        test_file = io.BytesIO(b"This is not an image")
        
        response = client.post(
            "/process-bill",
            files={"file": ("test.txt", test_file, "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]
    
    def test_process_bill_large_file(self):
        """Test processing with file that's too large"""
        # Create a large file (simulate 11MB)
        large_data = b"x" * (11 * 1024 * 1024)
        test_file = io.BytesIO(large_data)
        
        response = client.post(
            "/process-bill",
            files={"file": ("large.jpg", test_file, "image/jpeg")}
        )
        
        assert response.status_code == 400
        assert "File too large" in response.json()["detail"]
    
    @patch('main.mistral_service')
    def test_process_bill_success(self, mock_service):
        """Test successful bill processing"""
        # Mock the Mistral service response
        mock_bill_info = BillInfo(
            restaurant_name="Test Restaurant",
            total=25.50,
            currency="USD"
        )
        
        mock_service.process_image_from_bytes = AsyncMock(return_value={
            "status": ProcessingStatus.SUCCESS,
            "message": "Bill processed successfully",
            "bill_info": mock_bill_info,
            "raw_text": "Test OCR text"
        })
        
        # Create a test image
        test_image = self._create_test_image()
        
        response = client.post(
            "/process-bill",
            files={"file": ("test.jpg", test_image, "image/jpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Bill processed successfully"
        assert data["bill_info"]["restaurant_name"] == "Test Restaurant"
        assert data["bill_info"]["total"] == 25.50
        assert data["raw_text"] == "Test OCR text"
        assert "processing_time" in data
    
    @patch('main.mistral_service')
    def test_process_bill_error(self, mock_service):
        """Test bill processing with error"""
        # Mock the Mistral service to return an error
        mock_service.process_image_from_bytes = AsyncMock(return_value={
            "status": ProcessingStatus.ERROR,
            "message": "Processing failed",
            "bill_info": None,
            "raw_text": None,
            "error_details": "Mock error"
        })
        
        # Create a test image
        test_image = self._create_test_image()
        
        response = client.post(
            "/process-bill",
            files={"file": ("test.jpg", test_image, "image/jpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["message"] == "Processing failed"
        assert data["error_details"] == "Mock error"
    
    def test_process_bill_no_service(self):
        """Test processing when Mistral service is not available"""
        with patch('main.mistral_service', None):
            test_image = self._create_test_image()
            
            response = client.post(
                "/process-bill",
                files={"file": ("test.jpg", test_image, "image/jpeg")}
            )
            
            assert response.status_code == 500
            assert "Mistral OCR service is not available" in response.json()["detail"]
    
    def _create_test_image(self) -> io.BytesIO:
        """Create a test image for testing purposes"""
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes

def test_process_multiple_bills_success(client, mock_mistral_service):
    """Test successful processing of multiple bill images"""
    # Create test images
    test_image1 = create_test_image()
    test_image2 = create_test_image()
    
    response = client.post(
        "/process-multiple-bills",
        files=[
            ("files", ("bill1.jpg", test_image1, "image/jpeg")),
            ("files", ("bill2.jpg", test_image2, "image/jpeg"))
        ]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_images"] == 2
    assert data["successful_images"] == 2
    assert data["failed_images"] == 0
    assert len(data["bills"]) == 2
    assert "total_processing_time" in data
    assert len(data["errors"]) == 0

def test_process_multiple_bills_too_many_files(client):
    """Test rejection of too many files"""
    # Create 11 test images (exceeds limit of 10)
    files = []
    for i in range(11):
        test_image = create_test_image()
        files.append(("files", (f"bill{i}.jpg", test_image, "image/jpeg")))
    
    response = client.post("/process-multiple-bills", files=files)
    
    assert response.status_code == 400
    assert "Too many files" in response.json()["detail"]

def test_process_multiple_bills_no_files(client):
    """Test rejection when no files provided"""
    response = client.post("/process-multiple-bills", files=[])
    
    assert response.status_code == 422  # FastAPI validation error for empty list

def test_process_multiple_bills_mixed_results(client, mock_mistral_service):
    """Test processing multiple bills with mixed success/failure"""
    # Create test images with different types
    test_image_valid = create_test_image()
    test_image_invalid = b"not an image"
    
    response = client.post(
        "/process-multiple-bills",
        files=[
            ("files", ("valid_bill.jpg", test_image_valid, "image/jpeg")),
            ("files", ("invalid_bill.txt", test_image_invalid, "text/plain"))
        ]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_images"] == 2
    assert data["successful_images"] == 1
    assert data["failed_images"] == 1
    assert len(data["bills"]) == 1  # Only successful ones are included
    assert len(data["errors"]) == 1
    assert "Unsupported file type" in data["errors"][0]

def test_process_multiple_bills_large_files(client):
    """Test rejection of files that are too large"""
    # Create a large "image" (just bytes, but large)
    large_image = b"x" * (11 * 1024 * 1024)  # 11MB
    small_image = create_test_image()
    
    response = client.post(
        "/process-multiple-bills",
        files=[
            ("files", ("small_bill.jpg", small_image, "image/jpeg")),
            ("files", ("large_bill.jpg", large_image, "image/jpeg"))
        ]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_images"] == 2
    assert data["successful_images"] == 1
    assert data["failed_images"] == 1
    assert "File too large" in data["errors"][0]

if __name__ == "__main__":
    pytest.main([__file__])