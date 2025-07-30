from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_title: str = "TestPilot AI Backend"
    api_version: str = "0.1.0"
    debug: bool = False
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # LLM API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Database Configuration
    database_url: Optional[str] = None
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    
    # GCP Configuration
    gcp_project_id: Optional[str] = None
    gcp_region: str = "us-central1"
    gcp_zone: str = "us-central1-a"
    cloud_storage_bucket: Optional[str] = None
    
    # GCP Service Account (for local development)
    gcp_service_account_key_path: Optional[str] = None
    
    # JWT Configuration
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_access_token_expire_minutes: int = 30
    
    # Slack Configuration
    slack_signing_secret: Optional[str] = None
    slack_bot_token: Optional[str] = None
    slack_app_token: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Create global settings instance
settings = Settings() 