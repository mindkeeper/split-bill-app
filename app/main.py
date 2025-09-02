"""Main FastAPI application"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import time

from app.core.config import settings
from app.core.exceptions import (
    SplitBillException,
    RateLimitError,
    AuthenticationError,
    AuthorizationError,
    ServiceUnavailableError,
    ResourceNotFoundError,
    ConflictError,
    BadRequestError
)
from app.routers import health_router, ocr_router
from app.utils.response_utils import create_error_response, generate_request_id

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods_list,
    allow_headers=settings.cors_headers_list,
)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handlers
@app.exception_handler(RateLimitError)
async def rate_limit_exception_handler(request: Request, exc: RateLimitError):
    """Handle rate limit exceptions"""
    logger.warning(f"Rate limit exceeded: {exc.detail}")
    
    error_response = create_error_response(
        message=exc.detail,
        error_code="RATE_LIMIT_EXCEEDED",
        request_id=generate_request_id()
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json'),
        headers=exc.headers or {}
    )

@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication exceptions"""
    logger.warning(f"Authentication failed: {exc.detail}")
    
    error_response = create_error_response(
        message=exc.detail,
        error_code="AUTHENTICATION_FAILED",
        request_id=generate_request_id()
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json'),
        headers={"WWW-Authenticate": "Bearer"}
    )

@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request: Request, exc: AuthorizationError):
    """Handle authorization exceptions"""
    logger.warning(f"Authorization failed: {exc.detail}")
    
    error_response = create_error_response(
        message=exc.detail,
        error_code="ACCESS_DENIED",
        request_id=generate_request_id()
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )

@app.exception_handler(ServiceUnavailableError)
async def service_unavailable_exception_handler(request: Request, exc: ServiceUnavailableError):
    """Handle service unavailable exceptions"""
    logger.warning(f"Service unavailable: {exc.detail}")
    
    error_response = create_error_response(
        message=exc.detail,
        error_code="SERVICE_UNAVAILABLE",
        request_id=generate_request_id()
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )

@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_exception_handler(request: Request, exc: ResourceNotFoundError):
    """Handle resource not found exceptions"""
    logger.info(f"Resource not found: {exc.detail}")
    
    error_response = create_error_response(
        message=exc.detail,
        error_code="RESOURCE_NOT_FOUND",
        request_id=generate_request_id()
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )

@app.exception_handler(ConflictError)
async def conflict_exception_handler(request: Request, exc: ConflictError):
    """Handle conflict exceptions"""
    logger.warning(f"Conflict error: {exc.detail}")
    
    error_response = create_error_response(
        message=exc.detail,
        error_code="CONFLICT_ERROR",
        request_id=generate_request_id()
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )

@app.exception_handler(BadRequestError)
async def bad_request_exception_handler(request: Request, exc: BadRequestError):
    """Handle bad request exceptions"""
    logger.warning(f"Bad request: {exc.detail}")
    
    error_response = create_error_response(
        message=exc.detail,
        error_code="BAD_REQUEST",
        request_id=generate_request_id()
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )

@app.exception_handler(SplitBillException)
async def split_bill_exception_handler(request: Request, exc: SplitBillException):
    """Handle custom Split Bill exceptions (fallback for other custom exceptions)"""
    logger.warning(f"Split Bill exception: {exc.detail} (Status: {exc.status_code})")
    
    error_response = create_error_response(
        message=exc.detail,
        error_code="SPLIT_BILL_ERROR",
        request_id=generate_request_id()
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json'),
        headers=exc.headers or {}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "value": error.get("input")
        })
    
    error_response = create_error_response(
        message="Request validation failed",
        error_code="ValidationError",
        error_details={"validation_errors": validation_errors},
        request_id=generate_request_id()
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode='json')
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    error_response = create_error_response(
        message="An unexpected error occurred",
        error_code="InternalServerError",
        error_details={"error_type": exc.__class__.__name__},
        request_id=generate_request_id()
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )

# Include routers
app.include_router(health_router)
app.include_router(ocr_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "description": settings.app_description,
        "docs_url": "/docs",
        "health_check": "/health",
        "endpoints": {
            "process_bill": "/ocr/process-bill",
            "process_multiple_bills": "/ocr/process-multiple-bills",
            "upload_test": "/ocr/upload-test"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )