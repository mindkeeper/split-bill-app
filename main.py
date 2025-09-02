from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
import logging
import time
from models import OCRResponse, UploadResponse, ProcessingStatus, MultipleBillsResponse
from mistral_service import MistralOCRService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Mistral OCR service
try:
    mistral_service = MistralOCRService()
    logger.info("Mistral OCR service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Mistral OCR service: {str(e)}")
    mistral_service = None

# Initialize FastAPI app
app = FastAPI(
    title="Split Bill Backend API",
    description="Backend API for processing bill images using Mistral OCR",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Split Bill Backend API is running"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Split Bill Backend API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/process-bill": "Process bill image with OCR",
            "/docs": "API documentation"
        }
    }

# Image upload and processing endpoint
@app.post("/process-bill", response_model=OCRResponse)
async def process_bill_image(file: UploadFile = File(...)):
    """
    Process a bill image using Mistral OCR
    
    Args:
        file: Uploaded image file (JPEG, PNG, etc.)
        
    Returns:
        OCRResponse with extracted bill information
    """
    start_time = time.time()
    
    # Check if Mistral service is available
    if mistral_service is None:
        raise HTTPException(
            status_code=500,
            detail="Mistral OCR service is not available. Please check API key configuration."
        )
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size allowed: {max_size / (1024*1024):.1f}MB"
        )
    
    try:
        logger.info(f"Processing bill image: {file.filename} ({len(file_content)} bytes)")
        
        # Process the image with Mistral OCR
        result = await mistral_service.process_image_from_bytes(file_content, file.filename)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create response
        response = OCRResponse(
            status=result["status"],
            message=result["message"],
            bill_info=result.get("bill_info"),
            raw_text=result.get("raw_text"),
            processing_time=processing_time,
            error_details=result.get("error_details")
        )
        
        logger.info(f"Bill processing completed in {processing_time:.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"Error processing bill image: {str(e)}")
        processing_time = time.time() - start_time
        
        return OCRResponse(
            status=ProcessingStatus.ERROR,
            message="Failed to process bill image",
            processing_time=processing_time,
            error_details=str(e)
        )

# File upload test endpoint
@app.post("/process-multiple-bills", response_model=MultipleBillsResponse)
async def process_multiple_bills(files: List[UploadFile] = File(...)):
    """
    Process multiple bill images using Mistral OCR
    
    Args:
        files: List of uploaded image files (JPEG, PNG, etc.)
        
    Returns:
        MultipleBillsResponse with extracted bill information for all images
    """
    start_time = time.time()
    
    # Check if Mistral service is available
    if mistral_service is None:
        raise HTTPException(
            status_code=500,
            detail="Mistral OCR service is not available. Please check API key configuration."
        )
    
    # Validate maximum number of files (limit to 10 for performance)
    max_files = 10
    if len(files) > max_files:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Maximum {max_files} files allowed per request."
        )
    
    if len(files) == 0:
        raise HTTPException(
            status_code=400,
            detail="No files provided. Please upload at least one image."
        )
    
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    max_size = 10 * 1024 * 1024  # 10MB per file
    
    bills = []
    errors = []
    successful_count = 0
    failed_count = 0
    
    logger.info(f"Processing {len(files)} bill images")
    
    for i, file in enumerate(files):
        try:
            # Validate file type
            if file.content_type not in allowed_types:
                error_msg = f"File {i+1} ({file.filename}): Unsupported file type {file.content_type}"
                errors.append(error_msg)
                failed_count += 1
                continue
            
            # Validate file size
            file_content = await file.read()
            if len(file_content) > max_size:
                error_msg = f"File {i+1} ({file.filename}): File too large ({len(file_content)/(1024*1024):.1f}MB > {max_size/(1024*1024):.1f}MB)"
                errors.append(error_msg)
                failed_count += 1
                continue
            
            logger.info(f"Processing file {i+1}/{len(files)}: {file.filename} ({len(file_content)} bytes)")
            
            # Process the image with Mistral OCR
            result = await mistral_service.process_image_from_bytes(file_content, file.filename)
            
            # Create individual OCR response
            ocr_response = OCRResponse(
                status=result["status"],
                message=result["message"],
                bill_info=result.get("bill_info"),
                raw_text=result.get("raw_text"),
                processing_time=0,  # Individual timing not tracked in batch
                error_details=result.get("error_details")
            )
            
            bills.append(ocr_response)
            
            if result["status"] == ProcessingStatus.SUCCESS:
                successful_count += 1
            else:
                failed_count += 1
                errors.append(f"File {i+1} ({file.filename}): {result.get('error_details', 'Processing failed')}")
            
        except Exception as e:
            error_msg = f"File {i+1} ({file.filename}): {str(e)}"
            errors.append(error_msg)
            failed_count += 1
            logger.error(f"Error processing file {i+1}: {str(e)}")
    
    # Calculate total processing time
    total_processing_time = time.time() - start_time
    
    # Determine overall status
    if successful_count == len(files):
        overall_status = ProcessingStatus.SUCCESS
        overall_message = f"All {len(files)} images processed successfully"
    elif successful_count > 0:
        overall_status = ProcessingStatus.SUCCESS
        overall_message = f"{successful_count}/{len(files)} images processed successfully"
    else:
        overall_status = ProcessingStatus.ERROR
        overall_message = f"Failed to process any images ({failed_count} failures)"
    
    logger.info(f"Batch processing completed: {successful_count} successful, {failed_count} failed in {total_processing_time:.2f}s")
    
    return MultipleBillsResponse(
        status=overall_status,
        message=overall_message,
        total_images=len(files),
        successful_images=successful_count,
        failed_images=failed_count,
        bills=bills,
        total_processing_time=total_processing_time,
        errors=errors
    )

@app.post("/upload-test", response_model=UploadResponse)
async def upload_test(file: UploadFile = File(...)):
    """
    Test endpoint for file upload without processing
    
    Args:
        file: Uploaded file
        
    Returns:
        UploadResponse with file information
    """
    file_content = await file.read()
    
    return UploadResponse(
        filename=file.filename or "unknown",
        file_size=len(file_content),
        content_type=file.content_type or "unknown",
        message="File uploaded successfully"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)