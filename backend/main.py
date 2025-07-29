from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.config import settings
from app.api.health import router as health_router
from app.api.execution import router as execution_router
from app.api.test_generation import router as test_generation_router
from app.api.auth import router as auth_router

# Create FastAPI app instance
app = FastAPI(
    title=settings.api_title,
    description="AI-powered test generation and execution backend",
    version=settings.api_version,
    debug=settings.debug
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(execution_router)
app.include_router(test_generation_router)
app.include_router(auth_router)

@app.get("/")
async def root():
    """Root endpoint returning basic API information."""
    return {
        "message": "TestPilot AI Backend API",
        "version": settings.api_version,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "health_detailed": "/health/detailed",
            "ready": "/health/ready",
            "execution": "/execution",
            "execution_health": "/execution/health",
            "execute_test": "/execution/execute",
            "execute_test_async": "/execution/execute-async",
            "auth_login": "/api/v1/auth/login",
            "auth_me": "/api/v1/auth/me",
            "auth_refresh": "/api/v1/auth/refresh",
            "test_generation": "/api/v1/generate",
            "test_execution": "/api/v1/execute",
            "test_results": "/api/v1/results/{execution_id}"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    ) 