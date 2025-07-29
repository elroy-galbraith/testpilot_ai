from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.repositories.test_case_repository import TestCaseRepository
from app.repositories.execution_repository import ExecutionRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.services.cache_service import cache_service
from app.services.storage_service import storage_service
from app.models import TestCase, ExecutionResult, UserFeedback
import logging
import hashlib
import json

logger = logging.getLogger(__name__)

class PersistenceService:
    """Comprehensive persistence service integrating database, cache, and storage."""
    
    def __init__(self, db: Session):
        self.db = db
        self.test_case_repo = TestCaseRepository(db)
        self.execution_repo = ExecutionRepository(db)
        self.feedback_repo = FeedbackRepository(db)
    
    # Test Case Operations
    def create_test_case(self, test_case_data: Dict[str, Any]) -> Optional[TestCase]:
        """Create a new test case with caching."""
        try:
            # Create test case
            test_case = self.test_case_repo.create(test_case_data)
            
            # Cache the test case
            cache_key = f"test_case:{test_case.id}"
            cache_service.set(cache_key, {
                "id": test_case.id,
                "title": test_case.title,
                "status": test_case.status,
                "framework": test_case.framework,
                "created_at": test_case.created_at.isoformat() if test_case.created_at else None
            }, expire=3600)
            
            # Invalidate related caches
            cache_service.delete("test_cases:list")
            cache_service.delete("test_cases:stats")
            
            return test_case
        except Exception as e:
            logger.error(f"Error creating test case: {e}")
            return None
    
    def get_test_case(self, test_case_id: int) -> Optional[TestCase]:
        """Get a test case with caching."""
        # Try cache first
        cache_key = f"test_case:{test_case_id}"
        cached_data = cache_service.get(cache_key)
        
        if cached_data:
            # Return from database for full data
            return self.test_case_repo.get_by_id(test_case_id)
        
        # Get from database
        test_case = self.test_case_repo.get_by_id(test_case_id)
        
        if test_case:
            # Cache the result
            cache_service.set(cache_key, {
                "id": test_case.id,
                "title": test_case.title,
                "status": test_case.status,
                "framework": test_case.framework,
                "created_at": test_case.created_at.isoformat() if test_case.created_at else None
            }, expire=3600)
        
        return test_case
    
    def get_test_cases(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[TestCase]:
        """Get test cases with caching."""
        # Create cache key
        cache_key = f"test_cases:list:{skip}:{limit}:{status or 'all'}"
        cached_data = cache_service.get(cache_key)
        
        if cached_data:
            # Return cached IDs and fetch from database
            test_case_ids = cached_data.get("ids", [])
            return [self.test_case_repo.get_by_id(tid) for tid in test_case_ids if tid]
        
        # Get from database
        test_cases = self.test_case_repo.get_all(skip=skip, limit=limit, status=status)
        
        if test_cases:
            # Cache the result
            cache_service.set(cache_key, {
                "ids": [tc.id for tc in test_cases]
            }, expire=1800)
        
        return test_cases
    
    def update_test_case(self, test_case_id: int, update_data: Dict[str, Any]) -> Optional[TestCase]:
        """Update a test case with cache invalidation."""
        try:
            test_case = self.test_case_repo.update(test_case_id, update_data)
            
            if test_case:
                # Invalidate caches
                cache_service.delete(f"test_case:{test_case_id}")
                cache_service.delete("test_cases:list")
                cache_service.delete("test_cases:stats")
                
                # Invalidate execution cache
                cache_service.invalidate_test_case_cache(test_case_id)
            
            return test_case
        except Exception as e:
            logger.error(f"Error updating test case {test_case_id}: {e}")
            return None
    
    # Execution Result Operations
    def create_execution_result(self, execution_data: Dict[str, Any]) -> Optional[ExecutionResult]:
        """Create a new execution result with artifact storage."""
        try:
            # Create execution result
            execution = self.execution_repo.create(execution_data)
            
            # Handle artifact storage if provided
            if execution and execution_data.get("screenshot_data"):
                screenshot_url = storage_service.upload_screenshot(
                    execution.test_case_id,
                    execution_data["screenshot_data"],
                    f"screenshot_{execution.id}.png"
                )
                if screenshot_url:
                    self.execution_repo.update(execution.id, {"screenshot_path": screenshot_url})
            
            if execution and execution_data.get("video_data"):
                video_url = storage_service.upload_video(
                    execution.test_case_id,
                    execution_data["video_data"],
                    f"video_{execution.id}.mp4"
                )
                if video_url:
                    self.execution_repo.update(execution.id, {"video_path": video_url})
            
            if execution and execution_data.get("logs"):
                logs_url = storage_service.upload_logs(
                    execution.test_case_id,
                    execution_data["logs"],
                    f"logs_{execution.id}.txt"
                )
                if logs_url:
                    self.execution_repo.update(execution.id, {"logs": logs_url})
            
            # Cache the execution result
            cache_key = f"execution:{execution.id}"
            cache_service.set(cache_key, {
                "id": execution.id,
                "test_case_id": execution.test_case_id,
                "status": execution.status,
                "execution_time": execution.execution_time,
                "created_at": execution.created_at.isoformat() if execution.created_at else None
            }, expire=7200)
            
            # Invalidate test case cache
            cache_service.invalidate_test_case_cache(execution.test_case_id)
            
            return execution
        except Exception as e:
            logger.error(f"Error creating execution result: {e}")
            return None
    
    def get_execution_result(self, execution_id: int) -> Optional[ExecutionResult]:
        """Get an execution result with caching."""
        # Try cache first
        cache_key = f"execution:{execution_id}"
        cached_data = cache_service.get(cache_key)
        
        if cached_data:
            return self.execution_repo.get_by_id(execution_id)
        
        # Get from database
        execution = self.execution_repo.get_by_id(execution_id)
        
        if execution:
            # Cache the result
            cache_service.set(cache_key, {
                "id": execution.id,
                "test_case_id": execution.test_case_id,
                "status": execution.status,
                "execution_time": execution.execution_time,
                "created_at": execution.created_at.isoformat() if execution.created_at else None
            }, expire=7200)
        
        return execution
    
    def get_execution_results_for_test_case(self, test_case_id: int) -> List[ExecutionResult]:
        """Get all execution results for a test case."""
        return self.execution_repo.get_by_test_case_id(test_case_id)
    
    # User Feedback Operations
    def create_feedback(self, feedback_data: Dict[str, Any]) -> Optional[UserFeedback]:
        """Create a new user feedback with caching."""
        try:
            feedback = self.feedback_repo.create(feedback_data)
            
            if feedback:
                # Cache the feedback
                cache_key = f"feedback:{feedback.id}"
                cache_service.set(cache_key, {
                    "id": feedback.id,
                    "test_case_id": feedback.test_case_id,
                    "rating": feedback.rating,
                    "feedback_type": feedback.feedback_type,
                    "created_at": feedback.created_at.isoformat() if feedback.created_at else None
                }, expire=3600)
                
                # Invalidate related caches
                cache_service.delete(f"feedback:test_case:{feedback.test_case_id}")
                cache_service.delete("feedback:stats")
            
            return feedback
        except Exception as e:
            logger.error(f"Error creating feedback: {e}")
            return None
    
    def get_feedback_for_test_case(self, test_case_id: int) -> List[UserFeedback]:
        """Get all feedback for a test case with caching."""
        # Try cache first
        cache_key = f"feedback:test_case:{test_case_id}"
        cached_data = cache_service.get(cache_key)
        
        if cached_data:
            feedback_ids = cached_data.get("ids", [])
            return [self.feedback_repo.get_by_id(fid) for fid in feedback_ids if fid]
        
        # Get from database
        feedback_list = self.feedback_repo.get_by_test_case_id(test_case_id)
        
        if feedback_list:
            # Cache the result
            cache_service.set(cache_key, {
                "ids": [f.id for f in feedback_list]
            }, expire=1800)
        
        return feedback_list
    
    # Statistics and Analytics
    def get_test_case_stats(self) -> Dict[str, Any]:
        """Get test case statistics with caching."""
        cache_key = "test_cases:stats"
        cached_stats = cache_service.get(cache_key)
        
        if cached_stats:
            return cached_stats
        
        # Calculate stats
        stats = {
            "total_test_cases": self.db.query(TestCase).count(),
            "status_counts": self.test_case_repo.get_count_by_status(),
            "framework_counts": {}
        }
        
        # Get framework counts
        frameworks = self.db.query(TestCase.framework).distinct().all()
        for framework in frameworks:
            if framework[0]:
                count = self.db.query(TestCase).filter(TestCase.framework == framework[0]).count()
                stats["framework_counts"][framework[0]] = count
        
        # Cache the stats
        cache_service.set(cache_key, stats, expire=3600)
        
        return stats
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return self.execution_repo.get_execution_stats()
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback statistics with caching."""
        cache_key = "feedback:stats"
        cached_stats = cache_service.get(cache_key)
        
        if cached_stats:
            return cached_stats
        
        # Get stats from repository
        stats = self.feedback_repo.get_feedback_stats()
        
        # Cache the stats
        cache_service.set(cache_key, stats, expire=3600)
        
        return stats
    
    # Cleanup Operations
    def cleanup_test_case_artifacts(self, test_case_id: int) -> bool:
        """Clean up all artifacts for a test case."""
        try:
            # Clean up storage artifacts
            storage_service.cleanup_test_artifacts(test_case_id)
            
            # Invalidate caches
            cache_service.invalidate_test_case_cache(test_case_id)
            
            return True
        except Exception as e:
            logger.error(f"Error cleaning up artifacts for test case {test_case_id}: {e}")
            return False 