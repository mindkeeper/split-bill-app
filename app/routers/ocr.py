"""OCR processing router"""

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from typing import List
import time
import logging

from app.models.responses import OCRResponse, UploadResponse, MultipleBillsResponse
from app.core.dependencies import get_mistral_service
from app.core.exceptions import FileValidationError, OCRProcessingError
from app.services.mistral_service import MistralOCRService
from app.utils.file_validation import validate_image_file, get_file_info
from app.utils.response_utils import (
    create_ocr_response,
    create_upload_response,
    create_multiple_bills_response,
    generate_request_id
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ocr",
    tags=["ocr"]
)

@router.post("/process-bill", response_model=OCRResponse)
async def process_bill_image(
    file: UploadFile = File(...),
    mistral_service: MistralOCRService = Depends(get_mistral_service)
):
    """Process a single bill image using OCR
    
    Args:
        file: Uploaded image file
        mistral_service: Injected Mistral OCR service
        
    Returns:
        OCRResponse: Processed bill information
        
    Raises:
        HTTPException: If file validation or OCR processing fails
    """
    request_id = generate_request_id()
    start_time = time.time()
    
    try:
        # Validate file
        validate_image_file(file)
        logger.info(f"Processing bill image: {file.filename} (Request ID: {request_id})")
        
        # Read file content
        file_content = await file.read()
        
        # Process with Mistral OCR
        result = await mistral_service.process_image_from_bytes(file_content, file.filename)
        
        processing_time = time.time() - start_time
        
        return create_ocr_response(
            message="Bill processed successfully",
            bill_info=result.get("bill_info"),
            raw_text=result.get("raw_text"),
            processing_time=processing_time,
            request_id=request_id
        )
        
    except FileValidationError as e:
        logger.warning(f"File validation failed: {str(e)} (Request ID: {request_id})")
        raise e
    except OCRProcessingError as e:
        logger.error(f"OCR processing failed: {str(e)} (Request ID: {request_id})")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error processing bill: {str(e)} (Request ID: {request_id})")
        raise e

@router.post("/process-multiple-bills", response_model=MultipleBillsResponse)
async def process_multiple_bills(
    files: List[UploadFile] = File(...),
    mistral_service: MistralOCRService = Depends(get_mistral_service)
):
    """Process multiple bill images using OCR
    
    Args:
        files: List of uploaded image files
        mistral_service: Injected Mistral OCR service
        
    Returns:
        MultipleBillsResponse: Results for all processed bills
    """
    request_id = generate_request_id()
    start_time = time.time()
    
    if not files:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No files provided"
        )
    
    logger.info(f"Processing {len(files)} bill images (Request ID: {request_id})")
    
    bills = []
    errors = []
    successful_count = 0
    failed_count = 0
    
    for i, file in enumerate(files):
        try:
            # Validate file
            validate_image_file(file)
            
            # Read file content
            file_content = await file.read()
            
            # Process with Mistral OCR
            result = await mistral_service.process_image_from_bytes(file_content, file.filename)
            
            bills.append({
                "bill_info": result.get("bill_info"),
                "raw_text": result.get("raw_text"),
                "processing_time": None,  # Individual timing not tracked in batch
                "confidence_score": None
            })
            
            successful_count += 1
            logger.info(f"Successfully processed file {i+1}/{len(files)}: {file.filename}")
            
        except (FileValidationError, OCRProcessingError) as e:
            error_msg = f"File {file.filename}: {str(e)}"
            errors.append(error_msg)
            failed_count += 1
            logger.warning(f"Failed to process file {i+1}/{len(files)}: {error_msg}")
            
        except Exception as e:
            error_msg = f"File {file.filename}: Unexpected error - {str(e)}"
            errors.append(error_msg)
            failed_count += 1
            logger.error(f"Unexpected error processing file {i+1}/{len(files)}: {error_msg}")
    
    total_processing_time = time.time() - start_time
    
    message = f"Processed {successful_count}/{len(files)} bills successfully"
    if failed_count > 0:
        message += f", {failed_count} failed"
    
    return create_multiple_bills_response(
        message=message,
        total_images=len(files),
        successful_images=successful_count,
        failed_images=failed_count,
        bills=bills,
        total_processing_time=total_processing_time,
        errors=errors,
        request_id=request_id
    )

@router.post("/upload-test", response_model=UploadResponse)
async def upload_test(file: UploadFile = File(...)):
    """Test file upload without processing
    
    Args:
        file: Uploaded file
        
    Returns:
        UploadResponse: File upload information
    """
    request_id = generate_request_id()
    
    try:
        # Validate file
        validate_image_file(file)
        
        # Get file info
        file_info = get_file_info(file)
        
        # Read file to get actual size
        file_content = await file.read()
        actual_size = len(file_content)
        
        logger.info(f"File upload test successful: {file.filename} ({actual_size} bytes)")
        
        return create_upload_response(
            message="File uploaded and validated successfully",
            filename=file_info["filename"],
            file_size=actual_size,
            content_type=file_info["content_type"],
            request_id=request_id
        )
        
    except FileValidationError as e:
        logger.warning(f"File validation failed: {str(e)} (Request ID: {request_id})")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in upload test: {str(e)} (Request ID: {request_id})")
        raise e