from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional, Dict, Any
from app.models import ExecutionResult
import logging

logger = logging.getLogger(__name__)

class ExecutionRepository:
    """Repository for ExecutionResult database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, execution_data: Dict[str, Any]) -> ExecutionResult:
        """Create a new execution result."""
        try:
            execution = ExecutionResult(**execution_data)
            self.db.add(execution)
            self.db.commit()
            self.db.refresh(execution)
            logger.info(f"Created execution result with ID: {execution.id}")
            return execution
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating execution result: {e}")
            raise
    
    def get_by_id(self, execution_id: int) -> Optional[ExecutionResult]:
        """Get an execution result by ID."""
        try:
            return self.db.query(ExecutionResult).filter(ExecutionResult.id == execution_id).first()
        except Exception as e:
            logger.error(f"Error getting execution result {execution_id}: {e}")
            return None
    
    def get_by_test_case_id(self, test_case_id: int) -> List[ExecutionResult]:
        """Get all execution results for a test case."""
        try:
            return self.db.query(ExecutionResult).filter(
                ExecutionResult.test_case_id == test_case_id
            ).order_by(desc(ExecutionResult.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting execution results for test case {test_case_id}: {e}")
            return []
    
    def get_latest_by_test_case_id(self, test_case_id: int) -> Optional[ExecutionResult]:
        """Get the latest execution result for a test case."""
        try:
            return self.db.query(ExecutionResult).filter(
                ExecutionResult.test_case_id == test_case_id
            ).order_by(desc(ExecutionResult.created_at)).first()
        except Exception as e:
            logger.error(f"Error getting latest execution result for test case {test_case_id}: {e}")
            return None
    
    def update(self, execution_id: int, update_data: Dict[str, Any]) -> Optional[ExecutionResult]:
        """Update an execution result."""
        try:
            execution = self.get_by_id(execution_id)
            if not execution:
                return None
            
            for key, value in update_data.items():
                if hasattr(execution, key):
                    setattr(execution, key, value)
            
            self.db.commit()
            self.db.refresh(execution)
            logger.info(f"Updated execution result {execution_id}")
            return execution
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating execution result {execution_id}: {e}")
            return None
    
    def delete(self, execution_id: int) -> bool:
        """Delete an execution result."""
        try:
            execution = self.get_by_id(execution_id)
            if not execution:
                return False
            
            self.db.delete(execution)
            self.db.commit()
            logger.info(f"Deleted execution result {execution_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting execution result {execution_id}: {e}")
            return False
    
    def get_by_status(self, status: str) -> List[ExecutionResult]:
        """Get execution results by status."""
        try:
            return self.db.query(ExecutionResult).filter(
                ExecutionResult.status == status
            ).order_by(desc(ExecutionResult.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting execution results by status {status}: {e}")
            return []
    
    def get_failed_executions(self) -> List[ExecutionResult]:
        """Get all failed execution results."""
        try:
            return self.db.query(ExecutionResult).filter(
                ExecutionResult.status.in_(['failed', 'error', 'timeout'])
            ).order_by(desc(ExecutionResult.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting failed execution results: {e}")
            return []
    
    def get_execution_stats(self) -> Dict[str, int]:
        """Get execution statistics by status."""
        try:
            result = self.db.query(
                ExecutionResult.status, 
                self.db.func.count(ExecutionResult.id)
            ).group_by(ExecutionResult.status).all()
            return dict(result)
        except Exception as e:
            logger.error(f"Error getting execution statistics: {e}")
            return {} 