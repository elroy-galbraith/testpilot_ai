from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class TestCase(Base):
    """Model for storing test case specifications and generated code."""
    __tablename__ = "test_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    spec = Column(Text, nullable=False)  # Original product specification
    generated_code = Column(Text, nullable=True)  # Generated test code
    framework = Column(String(50), nullable=True)  # Test framework (e.g., Playwright, Selenium)
    language = Column(String(20), nullable=True)  # Programming language
    status = Column(String(20), default="pending")  # pending, generated, executed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    meta_data = Column(JSON, nullable=True)  # Additional metadata like tags, priority, etc.
    
    # Relationships
    execution_results = relationship("ExecutionResult", back_populates="test_case", cascade="all, delete-orphan")
    user_feedback = relationship("UserFeedback", back_populates="test_case", cascade="all, delete-orphan")

class ExecutionResult(Base):
    """Model for storing test execution results and artifacts."""
    __tablename__ = "execution_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False)
    status = Column(String(20), nullable=False)  # passed, failed, error, timeout
    execution_time = Column(Integer, nullable=True)  # Execution time in seconds
    error_message = Column(Text, nullable=True)  # Error details if failed
    screenshot_path = Column(String(500), nullable=True)  # Path to screenshot in Cloud Storage
    video_path = Column(String(500), nullable=True)  # Path to video recording in Cloud Storage
    logs = Column(Text, nullable=True)  # Execution logs
    browser_info = Column(JSON, nullable=True)  # Browser version, viewport, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    meta_data = Column(JSON, nullable=True)  # Additional execution metadata
    
    # Relationships
    test_case = relationship("TestCase", back_populates="execution_results")

class UserFeedback(Base):
    """Model for storing user feedback on generated tests."""
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 rating
    feedback_text = Column(Text, nullable=True)  # Detailed feedback
    feedback_type = Column(String(50), nullable=False)  # accuracy, readability, completeness, etc.
    user_id = Column(String(100), nullable=True)  # User identifier (if authenticated)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    meta_data = Column(JSON, nullable=True)  # Additional feedback metadata
    
    # Relationships
    test_case = relationship("TestCase", back_populates="user_feedback") 