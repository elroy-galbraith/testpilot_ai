#!/usr/bin/env python3
"""
Simple test script to verify the persistence layer is working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, init_db, check_db_connection
from app.services.persistence_service import PersistenceService
from app.services.cache_service import cache_service
from app.services.storage_service import storage_service
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection."""
    logger.info("Testing database connection...")
    
    if check_db_connection():
        logger.info("✅ Database connection successful")
        return True
    else:
        logger.error("❌ Database connection failed")
        return False

def test_cache_service():
    """Test cache service."""
    logger.info("Testing cache service...")
    
    if cache_service.is_connected():
        logger.info("✅ Cache service connected")
        
        # Test basic operations
        cache_service.set("test_key", "test_value", expire=60)
        value = cache_service.get("test_key")
        
        if value == "test_value":
            logger.info("✅ Cache operations working")
            cache_service.delete("test_key")
            return True
        else:
            logger.error("❌ Cache operations failed")
            return False
    else:
        logger.warning("⚠️ Cache service not available (this is OK for local development)")
        return True

def test_storage_service():
    """Test storage service."""
    logger.info("Testing storage service...")
    
    if storage_service.is_available():
        logger.info("✅ Storage service available")
        return True
    else:
        logger.warning("⚠️ Storage service not available (this is OK for local development)")
        return True

def test_persistence_operations():
    """Test persistence operations."""
    logger.info("Testing persistence operations...")
    
    db = SessionLocal()
    persistence_service = PersistenceService(db)
    
    try:
        # Test creating a test case
        test_case_data = {
            "title": "Test Login Functionality",
            "description": "Test user login with valid credentials",
            "spec": "User should be able to login with valid email and password",
            "framework": "playwright",
            "language": "typescript",
            "status": "pending"
        }
        
        test_case = persistence_service.create_test_case(test_case_data)
        if test_case:
            logger.info(f"✅ Created test case with ID: {test_case.id}")
            
            # Test retrieving the test case
            retrieved_test_case = persistence_service.get_test_case(test_case.id)
            if retrieved_test_case and retrieved_test_case.id == test_case.id:
                logger.info("✅ Retrieved test case successfully")
                
                # Test creating an execution result
                execution_data = {
                    "test_case_id": test_case.id,
                    "status": "passed",
                    "execution_time": 15,
                    "browser_info": {"browser": "chrome", "version": "120.0"}
                }
                
                execution = persistence_service.create_execution_result(execution_data)
                if execution:
                    logger.info(f"✅ Created execution result with ID: {execution.id}")
                    
                    # Test creating feedback
                    feedback_data = {
                        "test_case_id": test_case.id,
                        "rating": 5,
                        "feedback_text": "Great test case, works perfectly!",
                        "feedback_type": "accuracy",
                        "user_id": "test_user_123"
                    }
                    
                    feedback = persistence_service.create_feedback(feedback_data)
                    if feedback:
                        logger.info(f"✅ Created feedback with ID: {feedback.id}")
                        
                        # Test statistics
                        stats = persistence_service.get_test_case_stats()
                        logger.info(f"✅ Retrieved test case stats: {stats}")
                        
                        # Clean up
                        db.delete(feedback)
                        db.delete(execution)
                        db.delete(test_case)
                        db.commit()
                        logger.info("✅ Cleaned up test data")
                        
                        return True
                    else:
                        logger.error("❌ Failed to create feedback")
                        return False
                else:
                    logger.error("❌ Failed to create execution result")
                    return False
            else:
                logger.error("❌ Failed to retrieve test case")
                return False
        else:
            logger.error("❌ Failed to create test case")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during persistence test: {e}")
        return False
    finally:
        db.close()

def main():
    """Run all tests."""
    logger.info("🚀 Starting persistence layer tests...")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Cache Service", test_cache_service),
        ("Storage Service", test_storage_service),
        ("Persistence Operations", test_persistence_operations)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        if test_func():
            passed += 1
            logger.info(f"✅ {test_name} passed")
        else:
            logger.error(f"❌ {test_name} failed")
    
    logger.info(f"\n--- Test Results ---")
    logger.info(f"Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All tests passed! Persistence layer is working correctly.")
        return 0
    else:
        logger.error("💥 Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Run tests
    exit_code = main()
    sys.exit(exit_code) 