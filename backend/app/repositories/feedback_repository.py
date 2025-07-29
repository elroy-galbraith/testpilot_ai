from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional, Dict, Any
from app.models import UserFeedback
import logging

logger = logging.getLogger(__name__)

class FeedbackRepository:
    """Repository for UserFeedback database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, feedback_data: Dict[str, Any]) -> UserFeedback:
        """Create a new user feedback."""
        try:
            feedback = UserFeedback(**feedback_data)
            self.db.add(feedback)
            self.db.commit()
            self.db.refresh(feedback)
            logger.info(f"Created user feedback with ID: {feedback.id}")
            return feedback
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user feedback: {e}")
            raise
    
    def get_by_id(self, feedback_id: int) -> Optional[UserFeedback]:
        """Get a user feedback by ID."""
        try:
            return self.db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
        except Exception as e:
            logger.error(f"Error getting user feedback {feedback_id}: {e}")
            return None
    
    def get_by_test_case_id(self, test_case_id: int) -> List[UserFeedback]:
        """Get all feedback for a test case."""
        try:
            return self.db.query(UserFeedback).filter(
                UserFeedback.test_case_id == test_case_id
            ).order_by(desc(UserFeedback.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting feedback for test case {test_case_id}: {e}")
            return []
    
    def get_by_user_id(self, user_id: str) -> List[UserFeedback]:
        """Get all feedback by a specific user."""
        try:
            return self.db.query(UserFeedback).filter(
                UserFeedback.user_id == user_id
            ).order_by(desc(UserFeedback.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting feedback for user {user_id}: {e}")
            return []
    
    def update(self, feedback_id: int, update_data: Dict[str, Any]) -> Optional[UserFeedback]:
        """Update a user feedback."""
        try:
            feedback = self.get_by_id(feedback_id)
            if not feedback:
                return None
            
            for key, value in update_data.items():
                if hasattr(feedback, key):
                    setattr(feedback, key, value)
            
            self.db.commit()
            self.db.refresh(feedback)
            logger.info(f"Updated user feedback {feedback_id}")
            return feedback
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user feedback {feedback_id}: {e}")
            return None
    
    def delete(self, feedback_id: int) -> bool:
        """Delete a user feedback."""
        try:
            feedback = self.get_by_id(feedback_id)
            if not feedback:
                return False
            
            self.db.delete(feedback)
            self.db.commit()
            logger.info(f"Deleted user feedback {feedback_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting user feedback {feedback_id}: {e}")
            return False
    
    def get_by_rating(self, rating: int) -> List[UserFeedback]:
        """Get feedback by rating."""
        try:
            return self.db.query(UserFeedback).filter(
                UserFeedback.rating == rating
            ).order_by(desc(UserFeedback.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting feedback by rating {rating}: {e}")
            return []
    
    def get_by_feedback_type(self, feedback_type: str) -> List[UserFeedback]:
        """Get feedback by type."""
        try:
            return self.db.query(UserFeedback).filter(
                UserFeedback.feedback_type == feedback_type
            ).order_by(desc(UserFeedback.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting feedback by type {feedback_type}: {e}")
            return []
    
    def get_average_rating_by_test_case(self, test_case_id: int) -> Optional[float]:
        """Get average rating for a test case."""
        try:
            result = self.db.query(
                self.db.func.avg(UserFeedback.rating)
            ).filter(UserFeedback.test_case_id == test_case_id).scalar()
            return float(result) if result else None
        except Exception as e:
            logger.error(f"Error getting average rating for test case {test_case_id}: {e}")
            return None
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback statistics."""
        try:
            total_feedback = self.db.query(self.db.func.count(UserFeedback.id)).scalar()
            avg_rating = self.db.query(self.db.func.avg(UserFeedback.rating)).scalar()
            
            # Get rating distribution
            rating_distribution = self.db.query(
                UserFeedback.rating,
                self.db.func.count(UserFeedback.id)
            ).group_by(UserFeedback.rating).all()
            
            # Get feedback type distribution
            type_distribution = self.db.query(
                UserFeedback.feedback_type,
                self.db.func.count(UserFeedback.id)
            ).group_by(UserFeedback.feedback_type).all()
            
            return {
                "total_feedback": total_feedback,
                "average_rating": float(avg_rating) if avg_rating else 0,
                "rating_distribution": dict(rating_distribution),
                "type_distribution": dict(type_distribution)
            }
        except Exception as e:
            logger.error(f"Error getting feedback statistics: {e}")
            return {} 