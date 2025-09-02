"""Application configuration settings"""

import os
from typing import Optional, List
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    app_name: str = "Split Bill Backend API"
    app_description: str = "Backend API for processing bill images using Mistral OCR"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS Configuration
    cors_origins: str = "*"  # Configure properly for production
    cors_credentials: bool = True
    cors_methods: str = "*"
    cors_headers: str = "*"
    
    # Mistral API Configuration
    mistral_api_key: Optional[str] = os.getenv("MISTRAL_API_KEY")
    mistral_model: str = "mistral-ocr-latest"  # Mistral's OCR model
    
    # File Upload Configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: str = "image/jpeg,image/png,image/jpg"
    
    # Logging Configuration
    log_level: str = "INFO"
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert cors_origins string to list"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def cors_methods_list(self) -> List[str]:
        """Convert cors_methods string to list"""
        if self.cors_methods == "*":
            return ["*"]
        return [method.strip() for method in self.cors_methods.split(",")]
    
    @property
    def cors_headers_list(self) -> List[str]:
        """Convert cors_headers string to list"""
        if self.cors_headers == "*":
            return ["*"]
        return [header.strip() for header in self.cors_headers.split(",")]
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        """Convert allowed_file_types string to list"""
        return [file_type.strip() for file_type in self.allowed_file_types.split(",")]

# Global settings instance
settings = Settings()