"""Application dependencies for dependency injection"""

from fastapi import Depends, HTTPException, status
from app.services.mistral_service import MistralOCRService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Global service instances
_mistral_service: MistralOCRService = None

def get_mistral_service() -> MistralOCRService:
    """Get Mistral OCR service instance"""
    global _mistral_service
    
    if _mistral_service is None:
        try:
            _mistral_service = MistralOCRService()
            logger.info("Mistral OCR service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Mistral OCR service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OCR service is currently unavailable"
            )
    
    return _mistral_service

def validate_api_key() -> bool:
    """Validate that required API keys are configured"""
    if not settings.mistral_api_key or settings.mistral_api_key == "your_mistral_api_key_here":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mistral API key is not properly configured"
        )
    return True