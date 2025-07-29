from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from typing import List, Optional, Dict, Any
from app.models import TestCase
from app.database import get_db
import logging

logger = logging.getLogger(__name__)

class TestCaseRepository:
    """Repository for TestCase database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, test_case_data: Dict[str, Any]) -> TestCase:
        """Create a new test case."""
        try:
            test_case = TestCase(**test_case_data)
            self.db.add(test_case)
            self.db.commit()
            self.db.refresh(test_case)
            logger.info(f"Created test case with ID: {test_case.id}")
            return test_case
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating test case: {e}")
            raise
    
    def get_by_id(self, test_case_id: int) -> Optional[TestCase]:
        """Get a test case by ID."""
        try:
            return self.db.query(TestCase).filter(TestCase.id == test_case_id).first()
        except Exception as e:
            logger.error(f"Error getting test case {test_case_id}: {e}")
            return None
    
    def get_all(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[TestCase]:
        """Get all test cases with optional filtering."""
        try:
            query = self.db.query(TestCase)
            
            if status:
                query = query.filter(TestCase.status == status)
            
            return query.offset(skip).limit(limit).order_by(desc(TestCase.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting test cases: {e}")
            return []
    
    def update(self, test_case_id: int, update_data: Dict[str, Any]) -> Optional[TestCase]:
        """Update a test case."""
        try:
            test_case = self.get_by_id(test_case_id)
            if not test_case:
                return None
            
            for key, value in update_data.items():
                if hasattr(test_case, key):
                    setattr(test_case, key, value)
            
            self.db.commit()
            self.db.refresh(test_case)
            logger.info(f"Updated test case {test_case_id}")
            return test_case
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating test case {test_case_id}: {e}")
            return None
    
    def delete(self, test_case_id: int) -> bool:
        """Delete a test case."""
        try:
            test_case = self.get_by_id(test_case_id)
            if not test_case:
                return False
            
            self.db.delete(test_case)
            self.db.commit()
            logger.info(f"Deleted test case {test_case_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting test case {test_case_id}: {e}")
            return False
    
    def get_by_status(self, status: str) -> List[TestCase]:
        """Get test cases by status."""
        try:
            return self.db.query(TestCase).filter(TestCase.status == status).order_by(desc(TestCase.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting test cases by status {status}: {e}")
            return []
    
    def get_by_framework(self, framework: str) -> List[TestCase]:
        """Get test cases by framework."""
        try:
            return self.db.query(TestCase).filter(TestCase.framework == framework).order_by(desc(TestCase.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting test cases by framework {framework}: {e}")
            return []
    
    def search_by_title(self, title: str) -> List[TestCase]:
        """Search test cases by title."""
        try:
            return self.db.query(TestCase).filter(TestCase.title.ilike(f"%{title}%")).order_by(desc(TestCase.created_at)).all()
        except Exception as e:
            logger.error(f"Error searching test cases by title {title}: {e}")
            return []
    
    def get_count_by_status(self) -> Dict[str, int]:
        """Get count of test cases by status."""
        try:
            result = self.db.query(TestCase.status, func.count(TestCase.id)).group_by(TestCase.status).all()
            return dict(result)
        except Exception as e:
            logger.error(f"Error getting test case counts by status: {e}")
            return {} 