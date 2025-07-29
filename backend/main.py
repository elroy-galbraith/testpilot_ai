from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.config import settings
from app.api.health import router as health_router

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
            "ready": "/health/ready"
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