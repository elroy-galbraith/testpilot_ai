"""
FastAPI router for test generation and execution endpoints.
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.agent_service import AgentService
from app.services.execution_engine import execution_manager, ExecutionConfig
from app.repositories.test_case_repository import TestCaseRepository
from app.repositories.execution_repository import ExecutionRepository
from app.auth.jwt_auth import get_current_user, require_permissions, PERMISSIONS, AuthUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["test-generation"])

# Initialize services
agent_service = AgentService()


# Pydantic Schemas for Request Models
class GenerateRequest(BaseModel):
    """Request model for test generation."""
    spec: str = Field(..., description="Product specification for test generation", min_length=10)
    framework: str = Field("playwright", description="Testing framework (playwright, selenium, etc.)")
    language: str = Field("javascript", description="Programming language (javascript, python, etc.)")
    title: Optional[str] = Field(None, description="Optional title for the test case")
    description: Optional[str] = Field(None, description="Optional description for the test case")
    
    class Config:
        schema_extra = {
            "example": {
                "spec": "Create a login page with email and password fields. The page should validate inputs and show error messages for invalid credentials.",
                "framework": "playwright",
                "language": "javascript",
                "title": "Login Page Test",
                "description": "Test login functionality with validation"
            }
        }


class ExecuteRequest(BaseModel):
    """Request model for test execution."""
    test_case_id: int = Field(..., description="ID of the test case to execute")
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
    
    class Config:
        schema_extra = {
            "example": {
                "test_case_id": 1,
                "browser": "chromium",
                "headless": True,
                "timeout": 30000,
                "retry_count": 3,
                "retry_delay": 1000
            }
        }


# Pydantic Schemas for Response Models
class GenerateResponse(BaseModel):
    """Response model for test generation."""
    success: bool
    test_case_id: int
    title: str
    generated_code: str
    framework: str
    language: str
    status: str
    created_at: datetime
    message: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        from_attributes = True


class ExecuteResponse(BaseModel):
    """Response model for test execution."""
    success: bool
    execution_id: int
    test_case_id: int
    status: str
    job_id: Optional[str] = None
    message: str
    error: Optional[str] = None
    
    class Config:
        from_attributes = True


class ResultResponse(BaseModel):
    """Response model for execution results."""
    execution_id: int
    test_case_id: int
    status: str
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    video_path: Optional[str] = None
    logs: Optional[str] = None
    browser_info: Optional[Dict] = None
    created_at: datetime
    meta_data: Optional[Dict] = None
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    detail: Optional[str] = None
    status_code: int


# Dependency functions
def get_test_case_repository(db: Session = Depends(get_db)) -> TestCaseRepository:
    """Dependency to get TestCaseRepository instance."""
    return TestCaseRepository(db)


def get_execution_repository(db: Session = Depends(get_db)) -> ExecutionRepository:
    """Dependency to get ExecutionRepository instance."""
    return ExecutionRepository(db)


# API Endpoints
@router.post("/generate", response_model=GenerateResponse)
async def generate_test(
    request: GenerateRequest,
    test_case_repo: TestCaseRepository = Depends(get_test_case_repository)
):
    """
    Generate test cases from product specification.
    
    This endpoint accepts a product specification and generates test cases
    using the configured AI model and testing framework.
    """
    try:
        logger.info(f"Received test generation request for framework: {request.framework}")
        
        # Generate test cases using AgentService
        generation_result = agent_service.generate_test_cases(
            specification=request.spec,
            framework=request.framework,
            language=request.language
        )
        
        if not generation_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Test generation failed: {generation_result.get('error', 'Unknown error')}"
            )
        
        # Create test case in database
        test_case_data = {
            "title": request.title or f"Generated {request.framework.title()} Test",
            "description": request.description,
            "spec": request.spec,
            "generated_code": generation_result["test_cases"],
            "framework": request.framework,
            "language": request.language,
            "status": "generated",
            "meta_data": {
                "model_used": generation_result.get("model_used"),
                "generation_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        test_case = test_case_repo.create(test_case_data)
        
        response = GenerateResponse(
            success=True,
            test_case_id=test_case.id,
            title=test_case.title,
            generated_code=test_case.generated_code,
            framework=test_case.framework,
            language=test_case.language,
            status=test_case.status,
            created_at=test_case.created_at,
            message="Test case generated successfully"
        )
        
        logger.info(f"Test case generated successfully with ID: {test_case.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")


@router.post("/execute", response_model=ExecuteResponse)
async def execute_test(
    request: ExecuteRequest,
    background_tasks: BackgroundTasks,
    test_case_repo: TestCaseRepository = Depends(get_test_case_repository),
    execution_repo: ExecutionRepository = Depends(get_execution_repository)
):
    """
    Execute a test case.
    
    This endpoint accepts a test case ID and executes the test using the
    configured execution engine. Execution can be synchronous or asynchronous.
    """
    try:
        logger.info(f"Received execution request for test case ID: {request.test_case_id}")
        
        # Get the test case
        test_case = test_case_repo.get_by_id(request.test_case_id)
        if not test_case:
            raise HTTPException(status_code=404, detail="Test case not found")
        
        if not test_case.generated_code:
            raise HTTPException(status_code=400, detail="Test case has no generated code to execute")
        
        # Create execution record
        execution_data = {
            "test_case_id": test_case.id,
            "status": "queued",
            "meta_data": {
                "browser": request.browser,
                "headless": request.headless,
                "timeout": request.timeout,
                "retry_count": request.retry_count,
                "retry_delay": request.retry_delay,
                "viewport_width": request.viewport_width,
                "viewport_height": request.viewport_height,
                "user_agent": request.user_agent,
                "screenshot_on_failure": request.screenshot_on_failure,
                "capture_logs": request.capture_logs
            }
        }
        
        execution_result = execution_repo.create(execution_data)
        
        # Add execution to background tasks
        background_tasks.add_task(
            execute_test_background,
            test_case,
            execution_result,
            request,
            execution_repo
        )
        
        response = ExecuteResponse(
            success=True,
            execution_id=execution_result.id,
            test_case_id=test_case.id,
            status="queued",
            job_id=str(execution_result.id),
            message="Test execution has been queued"
        )
        
        logger.info(f"Test execution queued with ID: {execution_result.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")


@router.get("/test-cases")
async def get_test_cases(
    test_case_repo: TestCaseRepository = Depends(get_test_case_repository)
):
    """Get all test cases."""
    try:
        # For now, get all test cases since we don't have user system
        test_cases = test_case_repo.get_all()
        return [
            {
                "id": str(tc.id),
                "title": tc.title,
                "description": tc.description or "",
                "code": tc.generated_code,
                "framework": tc.framework,
                "language": tc.language,
                "status": tc.status,
                "createdAt": tc.created_at.isoformat() if tc.created_at else "",
                "updatedAt": tc.updated_at.isoformat() if tc.updated_at else ""
            }
            for tc in test_cases
        ]
    except Exception as e:
        logger.error(f"Error fetching test cases: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch test cases")


@router.get("/test-cases/{test_case_id}")
async def get_test_case(
    test_case_id: int,
    test_case_repo: TestCaseRepository = Depends(get_test_case_repository)
):
    """Get a specific test case by ID."""
    try:
        test_case = test_case_repo.get_by_id(test_case_id)
        if not test_case:
            raise HTTPException(status_code=404, detail="Test case not found")
        
        return {
            "id": str(test_case.id),
            "title": test_case.title,
            "description": test_case.description or "",
            "code": test_case.generated_code,
            "framework": test_case.framework,
            "language": test_case.language,
            "status": test_case.status,
            "createdAt": test_case.created_at.isoformat() if test_case.created_at else "",
            "updatedAt": test_case.updated_at.isoformat() if test_case.updated_at else ""
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching test case {test_case_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch test case")


@router.get("/results/{execution_id}", response_model=ResultResponse)
async def get_execution_results(
    execution_id: int,
    execution_repo: ExecutionRepository = Depends(get_execution_repository)
):
    """
    Get execution results by execution ID.
    
    This endpoint returns the current status and results of a test execution.
    """
    try:
        execution_result = execution_repo.get_by_id(execution_id)
        if not execution_result:
            raise HTTPException(status_code=404, detail="Execution result not found")
        
        response = ResultResponse(
            execution_id=execution_result.id,
            test_case_id=execution_result.test_case_id,
            status=execution_result.status,
            execution_time=execution_result.execution_time,
            error_message=execution_result.error_message,
            screenshot_path=execution_result.screenshot_path,
            video_path=execution_result.video_path,
            logs=execution_result.logs,
            browser_info=execution_result.browser_info,
            created_at=execution_result.created_at,
            meta_data=execution_result.meta_data
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution results for ID {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get execution results: {str(e)}")


async def execute_test_background(
    test_case,
    execution_result,
    request: ExecuteRequest,
    execution_repo: ExecutionRepository
):
    """Background task for test execution."""
    try:
        logger.info(f"Starting background execution for test case ID: {test_case.id}")
        
        # Update status to running
        execution_repo.update(execution_result.id, {"status": "running"})
        
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
            test_code=test_case.generated_code,
            config=config,
            test_id=str(execution_result.id)
        )
        
        # Update execution result with results
        update_data = {
            "status": "passed" if result.success else "failed",
            "execution_time": result.execution_time,
            "error_message": result.error_message,
            "screenshot_path": result.screenshot_path,
            "logs": str(result.console_logs) if result.console_logs else None,
            "browser_info": {
                "browser": request.browser,
                "viewport": f"{request.viewport_width}x{request.viewport_height}",
                "headless": request.headless
            }
        }
        
        execution_repo.update(execution_result.id, update_data)
        
        logger.info(f"Background execution completed for test case ID: {test_case.id}, success: {result.success}")
        
    except Exception as e:
        logger.error(f"Background execution failed for test case ID {test_case.id}: {e}")
        # Update status to failed
        execution_repo.update(execution_result.id, {
            "status": "error",
            "error_message": str(e)
        }) 