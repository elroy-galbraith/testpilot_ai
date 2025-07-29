"""Health check endpoints for the TestPilot AI Backend."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.config import settings
from app.services.agent_service import AgentService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Dictionary with basic health status
    """
    return {
        "status": "ok",
        "service": "TestPilot AI Backend",
        "version": settings.api_version
    }

@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check including all service dependencies.
    
    Returns:
        Dictionary with comprehensive health status
    """
    # Initialize services
    agent_service = AgentService()
    storage_service = StorageService()
    
    # Check LLM services
    llm_health = agent_service.health_check()
    
    # Check storage service
    storage_health = storage_service.health_check()
    
    # Determine overall status
    issues = []
    if not llm_health.get("test_query", False):
        issues.append("No LLM services configured")
    
    if not storage_health.get("available", False):
        issues.append("Cloud Storage not available")
    
    overall_status = "ok" if not issues else "degraded"
    
    return {
        "status": overall_status,
        "service": "TestPilot AI Backend",
        "version": settings.api_version,
        "environment": {
            "debug": settings.debug,
            "host": settings.host,
            "port": settings.port
        },
        "dependencies": {
            "llm_services": {
                "openai": {
                    "available": llm_health.get("openai", {}).get("available", False),
                    "configured": llm_health.get("openai", {}).get("configured", False)
                },
                "anthropic": {
                    "available": llm_health.get("anthropic", {}).get("available", False),
                    "configured": llm_health.get("anthropic", {}).get("configured", False)
                },
                "test_query": llm_health.get("test_query", False)
            },
            "database": {
                "configured": bool(settings.database_url),
                "url": settings.database_url or "Not configured"
            },
            "redis": {
                "configured": True,
                "url": settings.redis_url
            },
            "gcp": {
                "configured": bool(settings.gcp_project_id),
                "project_id": settings.gcp_project_id,
                "region": settings.gcp_region,
                "cloud_storage": storage_health
            }
        },
        "timestamp": "2025-07-29T13:50:00Z",
        "issues": issues
    }

@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check for deployment.
    
    Returns:
        Dictionary with readiness status
    """
    # Initialize services
    agent_service = AgentService()
    storage_service = StorageService()
    
    # Check LLM services
    llm_health = agent_service.health_check()
    
    # Check storage service
    storage_health = storage_service.health_check()
    
    # Determine if ready
    ready = True
    reason = None
    
    if not llm_health.get("test_query", False):
        ready = False
        reason = "No LLM services configured"
    elif not storage_health.get("available", False):
        ready = False
        reason = "Cloud Storage not available"
    
    return {
        "ready": ready,
        "status": "ready" if ready else "not_ready",
        "reason": reason
    } 