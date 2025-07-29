"""
FastAPI router for Playwright execution engine endpoints.
"""

import json
import logging
from typing import Dict, Optional
import time

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from app.services.execution_engine import (
    ExecutionConfig,
    ExecutionResult,
    execution_manager
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/execution", tags=["execution"])


class ExecutionRequest(BaseModel):
    """Request model for test execution."""
    test_code: str = Field(..., description="Playwright test script to execute")
    test_id: Optional[str] = Field(None, description="Optional test identifier")
    browser: str = Field("chromium", description="Browser to use (chromium, firefox, webkit)")
    headless: bool = Field(True, description="Run in headless mode")
    timeout: int = Field(30000, description="Test timeout in milliseconds")
    retry_count: int = Field(3, description="Number of retry attempts")
    retry_delay: int = Field(1000, description="Delay between retries in milliseconds")
    viewport_width: int = Field(1280, description="Viewport width")
    viewport_height: int = Field(720, description="Viewport height")
    user_agent: Optional[str] = Field(None, description="Custom user agent string")
    screenshot_on_failure: bool = Field(True, description="Capture screenshot on failure")
    capture_logs: bool = Field(True, description="Capture console and network logs")


class ExecutionResponse(BaseModel):
    """Response model for test execution."""
    success: bool
    test_id: str
    execution_time: float
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    console_logs: list = []
    network_logs: list = []
    metadata: Dict = {}


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str = "1.0.0"
    environment: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for the execution engine."""
    return HealthResponse(
        status="healthy",
        service="playwright-execution-engine",
        environment="staging"
    )


@router.post("/execute", response_model=ExecutionResponse)
async def execute_test(
    request: ExecutionRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute a Playwright test script.
    
    This endpoint accepts a Playwright test script and executes it
    using the configured browser with retry logic and artifact capture.
    """
    try:
        logger.info(f"Received execution request for test_id: {request.test_id}")
        
        # Create execution configuration
        config = ExecutionConfig(
            browser=request.browser,
            headless=request.headless,
            timeout=request.timeout,
            retry_count=request.retry_count,
            retry_delay=request.retry_delay,
            viewport_width=request.viewport_width,
            viewport_height=request.viewport_height,
            user_agent=request.user_agent,
            screenshot_on_failure=request.screenshot_on_failure,
            capture_logs=request.capture_logs
        )
        
        # Execute the test
        result = await execution_manager.execute_test(
            test_code=request.test_code,
            config=config,
            test_id=request.test_id
        )
        
        # Convert to response model
        response = ExecutionResponse(
            success=result.success,
            test_id=result.test_id,
            execution_time=result.execution_time,
            error_message=result.error_message,
            screenshot_path=result.screenshot_path,
            console_logs=result.console_logs,
            network_logs=result.network_logs,
            metadata=result.metadata
        )
        
        logger.info(f"Execution completed for test_id: {result.test_id}, success: {result.success}")
        return response
        
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.post("/execute-async")
async def execute_test_async(
    request: ExecutionRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute a Playwright test script asynchronously.
    
    This endpoint queues the test for execution and returns immediately
    with a job ID. The actual execution happens in the background.
    """
    try:
        test_id = request.test_id or f"async_{int(time.time())}"
        logger.info(f"Queuing async execution for test_id: {test_id}")
        
        # Add execution to background tasks
        background_tasks.add_task(
            execute_test_background,
            request,
            test_id
        )
        
        return {
            "job_id": test_id,
            "status": "queued",
            "message": "Test execution has been queued"
        }
        
    except Exception as e:
        logger.error(f"Failed to queue execution: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to queue execution: {str(e)}")


async def execute_test_background(request: ExecutionRequest, test_id: str):
    """Background task for test execution."""
    try:
        logger.info(f"Starting background execution for test_id: {test_id}")
        
        # Create execution configuration
        config = ExecutionConfig(
            browser=request.browser,
            headless=request.headless,
            timeout=request.timeout,
            retry_count=request.retry_count,
            retry_delay=request.retry_delay,
            viewport_width=request.viewport_width,
            viewport_height=request.viewport_height,
            user_agent=request.user_agent,
            screenshot_on_failure=request.screenshot_on_failure,
            capture_logs=request.capture_logs
        )
        
        # Execute the test
        result = await execution_manager.execute_test(
            test_code=request.test_code,
            config=config,
            test_id=test_id
        )
        
        logger.info(f"Background execution completed for test_id: {test_id}, success: {result.success}")
        
        # Here you could store the result in a database or send a notification
        # For now, we'll just log it
        
    except Exception as e:
        logger.error(f"Background execution failed for test_id {test_id}: {e}")


@router.get("/status/{test_id}")
async def get_execution_status(test_id: str):
    """
    Get the status of a test execution.
    
    This endpoint returns the current status and results of a test execution.
    """
    try:
        # In a real implementation, you would query a database or cache
        # for the execution status. For now, we'll return a placeholder.
        
        return {
            "test_id": test_id,
            "status": "completed",  # This would be dynamic
            "message": "Status endpoint not fully implemented yet"
        }
        
    except Exception as e:
        logger.error(f"Failed to get status for test_id {test_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.delete("/cleanup")
async def cleanup_execution_engines():
    """
    Clean up all execution engines.
    
    This endpoint cleans up all running execution engines and their resources.
    """
    try:
        await execution_manager.cleanup()
        return {
            "message": "All execution engines cleaned up successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup execution engines: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup: {str(e)}") 