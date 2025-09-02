"""Health check router"""

from fastapi import APIRouter, Depends
from app.models.responses import HealthResponse
from app.core.config import settings
from app.core.dependencies import get_mistral_service, validate_api_key
from app.utils.response_utils import create_health_response
from app.services.mistral_service import MistralOCRService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["health"]
)

@router.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check if API key is configured
        validate_api_key()
        api_key_status = "configured"
    except Exception:
        api_key_status = "not_configured"
    
    try:
        # Check Mistral service
        mistral_service = get_mistral_service()
        mistral_status = "available"
    except Exception as e:
        logger.warning(f"Mistral service check failed: {str(e)}")
        mistral_status = "unavailable"
    
    services = {
        "mistral_ocr": mistral_status,
        "api_key": api_key_status
    }
    
    overall_status = "healthy" if all(status in ["available", "configured"] for status in services.values()) else "degraded"
    
    return create_health_response(
        status=overall_status,
        message=f"{settings.app_name} is running",
        version=settings.app_version,
        services=services
    )

@router.get("/detailed", response_model=HealthResponse)
async def detailed_health_check(
    mistral_service: MistralOCRService = Depends(get_mistral_service)
):
    """Detailed health check with service validation"""
    services = {
        "mistral_ocr": "available",
        "api_key": "configured",
        "ocr_model": mistral_service.model
    }
    
    return create_health_response(
        status="healthy",
        message=f"{settings.app_name} - All services operational",
        version=settings.app_version,
        services=services
    )