import os
import logging
import tempfile
import aiofiles
from typing import Optional, Dict, Any
from mistralai import Mistral
from app.models.schemas import BillInfo, ProcessingStatus
import json
import re
import base64
from app.core.config import settings
from app.core.exceptions import OCRProcessingError, APIKeyError, ServiceUnavailableError, AuthorizationError, RateLimitError
from app.models.schemas import BillInfo, BillItem, ProcessingStatus

logger = logging.getLogger(__name__)

class MistralOCRService:
    """Service for handling Mistral OCR operations"""

    def __init__(self):
        self.api_key = settings.mistral_api_key
        if not self.api_key or self.api_key == "your_mistral_api_key_here":
            raise APIKeyError("Mistral API key not configured. Please set MISTRAL_API_KEY environment variable.")

        try:
            logger.info("Initializing Mistral client...")
            self.client = Mistral(api_key=self.api_key)
            logger.info(f"Mistral client initialized successfully. Client type: {type(self.client)}")

            # Use the correct model name for OCR
            self.model = "mistral-ocr-latest"  # Mistral's OCR model
            logger.info(f"Mistral OCR service initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Mistral client: {e}")
            raise OCRProcessingError(f"Failed to initialize Mistral client: {e}")

    async def process_image_from_bytes(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Process image bytes using Mistral OCR

        Args:
            image_bytes: Raw image bytes
            filename: Original filename

        Returns:
            Dict containing OCR results and extracted information
        """
        try:
            # Create temporary file to save the image
            logger.info(f"Processing image with filename: {filename}")
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                temp_file.write(image_bytes)
                temp_file_path = temp_file.name

            try:
                # Process with Mistral OCR
                result = await self._process_with_mistral(temp_file_path)
                return result
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

        except (ServiceUnavailableError, AuthorizationError, RateLimitError) as e:
            # Re-raise authentication/authorization/rate limit errors to be handled by FastAPI
            logger.error(f"API error processing image: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return {
                "status": ProcessingStatus.ERROR,
                "message": f"Failed to process image: {str(e)}",
                "raw_text": None,
                "bill_info": None,
                "error_details": str(e)
            }

    async def _process_with_mistral(self, image_path: str) -> Dict[str, Any]:
        """
        Process image using Mistral's vision model for OCR

        Args:
            image_path: Path to the image file

        Returns:
            Dict containing processing results
        """
        try:
            # Read image file as base64
            async with aiofiles.open(image_path, 'rb') as f:
                image_data = await f.read()

            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # Determine image format from file extension
            file_ext = os.path.splitext(image_path)[1].lower()
            if file_ext in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            elif file_ext == '.png':
                mime_type = 'image/png'
            elif file_ext == '.webp':
                mime_type = 'image/webp'
            else:
                mime_type = 'image/jpeg'  # Default fallback

            # Use Mistral's OCR API
            ocr_response = self.client.ocr.process(
                model=self.model,
                document={
                    "type": "image_url",
                    "image_url": f"data:{mime_type};base64,{image_base64}"
                },
                include_image_base64=True
            )

            # Extract text from OCR response
            raw_text = ""
            if hasattr(ocr_response, 'text'):
                raw_text = ocr_response.text
            elif hasattr(ocr_response, 'content'):
                raw_text = ocr_response.content
            else:
                raw_text = str(ocr_response)
            
            if not raw_text or raw_text.strip() == "":
                raise Exception("No text extracted from image")

            logger.info(f"Mistral OCR response: {raw_text}")

            # Parse bill information from OCR text using LLM
            bill_info = await self._extract_bill_info_from_text(raw_text)

            return {
                "status": ProcessingStatus.SUCCESS,
                "message": "Bill processed successfully",
                "raw_text": raw_text,
                "bill_info": bill_info,
                "ocr_metadata": {
                    "model": self.model,
                    "usage": ocr_response.usage.__dict__ if hasattr(ocr_response, 'usage') else None
                }
            }

        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in Mistral OCR processing: {error_message}")
            
            # Check for authentication errors (401 Unauthorized) - treat as service unavailable
            if "401" in error_message or "Unauthorized" in error_message:
                from app.core.exceptions import ServiceUnavailableError
                raise ServiceUnavailableError("OCR service temporarily unavailable. Please try again later.")
            
            # Check for other API errors that should be handled differently
            elif "403" in error_message or "Forbidden" in error_message:
                from app.core.exceptions import AuthorizationError
                raise AuthorizationError("Mistral API access forbidden. Please check your API permissions.")
            
            elif "429" in error_message or "rate limit" in error_message.lower():
                from app.core.exceptions import RateLimitError
                raise RateLimitError("Mistral", retry_after=60)
            
            # For all other errors, use OCRProcessingError
            else:
                raise OCRProcessingError(f"Mistral OCR processing failed: {error_message}")

    async def _extract_bill_info_from_text(self, ocr_text: str) -> Optional[BillInfo]:
        """
        Extract structured bill information from OCR text using Mistral LLM

        Args:
            ocr_text: Raw text extracted from OCR

        Returns:
            BillInfo object or None if extraction fails
        """
        try:
            if not ocr_text or ocr_text.strip() == "":
                logger.warning("Empty OCR text provided")
                return BillInfo(additional_info={"raw_ocr_text": ocr_text})

            # Create structured prompt for bill information extraction
            prompt = f"""
            Please analyze the following bill/receipt text and extract information in JSON format.

            OCR Text:
            {ocr_text}

            Extract the following information and return ONLY a valid JSON object:
            {{
                "restaurant_name": "name of the establishment or null",
                "date": "date of the bill in YYYY-MM-DD format or null",
                "time": "time of the bill in HH:MM format or null",
                "items": [
                    {{
                        "name": "item name",
                        "price": 0.00,
                        "quantity": 1
                    }}
                ],
                "subtotal": 0.00,
                "tax": 0.00,
                "tip": 0.00,
                "total": 0.00,
                "currency": "USD or detected currency"
            }}

            Rules:
            - Extract all visible items with their prices and quantities
            - Use null for any information that is not clearly visible
            - Ensure all prices are numbers (not strings)
            - Return ONLY the JSON object, no additional text
            """

            # Use Mistral LLM for structured extraction
            response = self.client.chat.complete(
                model="mistral-large-latest",  # Use latest large model for better extraction
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1  # Low temperature for consistent extraction
            )

            # Extract the response text
            response_text = response.choices[0].message.content
            logger.info(f"Bill extraction response: {response_text}")

            # Parse the JSON response
            return self._parse_bill_info(response_text)

        except Exception as e:
            logger.error(f"Error extracting bill info from text: {str(e)}")
            return BillInfo(additional_info={"raw_ocr_text": ocr_text, "extraction_error": str(e)})

    def _parse_bill_info(self, raw_text: str) -> Optional[BillInfo]:
        """
        Parse the raw OCR text to extract structured bill information

        Args:
            raw_text: Raw text from OCR

        Returns:
            BillInfo object or None if parsing fails
        """
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                bill_data = json.loads(json_str)

                # Convert to BillInfo model
                return BillInfo(**bill_data)
            else:
                # If no JSON found, create a basic BillInfo with raw text
                logger.warning("No JSON found in OCR response, creating basic bill info")
                return BillInfo(
                    additional_info={"raw_ocr_text": raw_text}
                )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OCR response: {str(e)}")
            return BillInfo(
                additional_info={"raw_ocr_text": raw_text, "parse_error": str(e)}
            )
        except Exception as e:
            logger.error(f"Error parsing bill info: {str(e)}")
            return BillInfo(
                additional_info={"raw_ocr_text": raw_text, "error": str(e)}
            )
