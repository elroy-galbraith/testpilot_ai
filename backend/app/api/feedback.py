from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/v1", tags=["feedback"])

class FeedbackRequest(BaseModel):
    test_case_id: str
    execution_id: str
    rating: int
    comments: str
    metadata: Optional[Dict[str, Any]] = None

class FeedbackResponse(BaseModel):
    id: str
    test_case_id: str
    execution_id: str
    rating: int
    comments: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    user_id: Optional[str] = None

class FeedbackCreateResponse(BaseModel):
    id: str
    message: str

# In-memory storage for feedback (replace with database in production)
feedback_storage = {}

@router.post("/feedback", response_model=FeedbackCreateResponse)
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit feedback for a test execution.
    
    Args:
        feedback: The feedback data including rating, comments, and metadata
    
    Returns:
        FeedbackCreateResponse: Confirmation of feedback submission
    """
    try:
        # Validate rating
        if not 1 <= feedback.rating <= 5:
            raise HTTPException(
                status_code=400, 
                detail="Rating must be between 1 and 5"
            )
        
        # Validate comments
        if len(feedback.comments.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Comments must be at least 10 characters long"
            )
        
        # Create feedback record
        feedback_id = str(uuid.uuid4())
        feedback_record = FeedbackResponse(
            id=feedback_id,
            test_case_id=feedback.test_case_id,
            execution_id=feedback.execution_id,
            rating=feedback.rating,
            comments=feedback.comments,
            metadata=feedback.metadata or {},
            created_at=datetime.utcnow(),
            user_id=None  # No user system implemented yet
        )
        
        # Store feedback (in production, save to database)
        feedback_storage[feedback_id] = feedback_record.dict()
        
        # TODO: In production, you might want to:
        # 1. Save to database
        # 2. Trigger notifications
        # 3. Update test case metrics
        # 4. Send to analytics service
        
        return FeedbackCreateResponse(
            id=feedback_id,
            message="Feedback submitted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit feedback: {str(e)}"
        )

@router.get("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(feedback_id: str):
    """
    Retrieve feedback by ID.
    
    Args:
        feedback_id: The ID of the feedback to retrieve
    
    Returns:
        FeedbackResponse: The feedback data
    """
    if feedback_id not in feedback_storage:
        raise HTTPException(
            status_code=404,
            detail="Feedback not found"
        )
    
    return FeedbackResponse(**feedback_storage[feedback_id])

@router.get("/feedback/test-case/{test_case_id}", response_model=list[FeedbackResponse])
async def get_feedback_by_test_case(test_case_id: str):
    """
    Retrieve all feedback for a specific test case.
    
    Args:
        test_case_id: The ID of the test case
    
    Returns:
        List[FeedbackResponse]: List of feedback for the test case
    """
    feedback_list = []
    for feedback_data in feedback_storage.values():
        if feedback_data["test_case_id"] == test_case_id:
            feedback_list.append(FeedbackResponse(**feedback_data))
    
    return feedback_list

@router.get("/feedback/execution/{execution_id}", response_model=list[FeedbackResponse])
async def get_feedback_by_execution(execution_id: str):
    """
    Retrieve all feedback for a specific execution.
    
    Args:
        execution_id: The ID of the execution
    
    Returns:
        List[FeedbackResponse]: List of feedback for the execution
    """
    feedback_list = []
    for feedback_data in feedback_storage.values():
        if feedback_data["execution_id"] == execution_id:
            feedback_list.append(FeedbackResponse(**feedback_data))
    
    return feedback_list 