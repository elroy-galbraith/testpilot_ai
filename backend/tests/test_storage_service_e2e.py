"""
End-to-end tests for GCP Cloud Storage service with mocked components.

These tests validate the complete artifact storage flow including:
- Upload operations with retry logic
- Error handling and logging
- Integration with database operations
- Notification systems
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import tempfile
import os
import time
from io import BytesIO
from datetime import datetime, timedelta

from google.cloud.exceptions import ServerError, TooManyRequests, GoogleCloudError
from google.cloud import storage

from app.services.storage_service import StorageService, retry_with_backoff, _calculate_backoff_delay
from app.models import ExecutionResult
from app.services.persistence_service import PersistenceService
from app.services.slack_service import SlackService


class TestStorageServiceE2E(unittest.TestCase):
    """End-to-end tests for storage service with mocked GCP Cloud Storage."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_bucket_name = "test-bucket"
        self.test_project_id = "test-project"
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'GCS_RETRY_INITIAL_DELAY': '0.1',
            'GCS_RETRY_MULTIPLIER': '2.0',
            'GCS_RETRY_MAX_DELAY': '1.0',
            'GCS_RETRY_MAX_ATTEMPTS': '3',
            'GCS_RETRY_JITTER': '0.1'
        })
        self.env_patcher.start()
        
        # Mock settings
        self.settings_patcher = patch('app.services.storage_service.settings')
        self.mock_settings = self.settings_patcher.start()
        self.mock_settings.cloud_storage_bucket = self.test_bucket_name
        self.mock_settings.gcp_service_account_key_path = None
        
        # Mock Google Cloud Storage client
        self.client_patcher = patch('app.services.storage_service.storage.Client')
        self.mock_client_class = self.client_patcher.start()
        
        # Create mock client and bucket
        self.mock_client = Mock()
        self.mock_bucket = Mock()
        self.mock_client_class.return_value = self.mock_client
        self.mock_client.bucket.return_value = self.mock_bucket
        
        # Mock bucket operations
        self.mock_bucket.reload.return_value = None
        
        # Create storage service instance
        self.storage_service = StorageService()
        
        # Mock database session
        self.mock_db_session = Mock()
        
        # Mock repositories
        self.mock_test_case_repo = Mock()
        self.mock_execution_repo = Mock()
        self.mock_feedback_repo = Mock()
        
        # Mock cache service
        self.mock_cache_service = Mock()
        
        # Create persistence service with mocked dependencies
        with patch('app.services.persistence_service.TestCaseRepository', return_value=self.mock_test_case_repo), \
             patch('app.services.persistence_service.ExecutionRepository', return_value=self.mock_execution_repo), \
             patch('app.services.persistence_service.FeedbackRepository', return_value=self.mock_feedback_repo), \
             patch('app.services.persistence_service.cache_service', self.mock_cache_service):
            
            self.persistence_service = PersistenceService(self.mock_db_session)
        
        # Mock Slack service
        self.mock_slack_service = Mock()
        self.mock_slack_service.is_available.return_value = True
        self.mock_slack_service.send_message.return_value = True
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()
        self.settings_patcher.stop()
        self.client_patcher.stop()
        
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_successful_upload_flow(self):
        """Test successful upload flow with database integration."""
        # Arrange
        test_case_id = 123
        screenshot_data = b"fake_screenshot_data"
        filename = "test_screenshot.png"
        expected_url = f"https://storage.googleapis.com/{self.test_bucket_name}/screenshots/{test_case_id}/{filename}"
        
        # Mock blob operations
        mock_blob = Mock()
        mock_blob.public_url = expected_url
        self.mock_bucket.blob.return_value = mock_blob
        
        # Mock execution result
        mock_execution = Mock(spec=ExecutionResult)
        mock_execution.id = 456
        mock_execution.test_case_id = test_case_id
        self.mock_execution_repo.create.return_value = mock_execution
        self.mock_execution_repo.update.return_value = mock_execution
        
        # Act
        with patch('app.services.persistence_service.storage_service', self.storage_service):
            result = self.persistence_service.create_execution_result({
                "test_case_id": test_case_id,
                "status": "completed",
                "screenshot_data": screenshot_data
            })
        
        # Assert
        self.assertIsNotNone(result)
        self.mock_execution_repo.create.assert_called_once()
        self.mock_execution_repo.update.assert_called_with(
            mock_execution.id, 
            {"screenshot_path": expected_url}
        )
        
        # Verify blob operations
        expected_blob_path = f"screenshots/{test_case_id}/screenshot_{mock_execution.id}.png"
        self.mock_bucket.blob.assert_called_with(expected_blob_path)
        mock_blob.upload_from_string.assert_called_once_with(screenshot_data)
        mock_blob.make_public.assert_called_once()
    
    def test_upload_with_transient_failures_and_retry(self):
        """Test upload with transient failures that trigger retry logic."""
        # Arrange
        test_case_id = 789
        screenshot_data = b"fake_screenshot_data"
        filename = "test_screenshot.png"
        expected_url = f"https://storage.googleapis.com/{self.test_bucket_name}/screenshots/{test_case_id}/{filename}"
        
        # Mock blob that fails twice then succeeds
        mock_blob = Mock()
        mock_blob.public_url = expected_url
        
        # Simulate transient failures
        mock_blob.upload_from_string.side_effect = [
            ServerError("Temporary server error"),
            TooManyRequests("Rate limit exceeded"),
            None  # Success on third attempt
        ]
        
        self.mock_bucket.blob.return_value = mock_blob
        
        # Act
        result = self.storage_service.upload_screenshot(test_case_id, screenshot_data, filename)
        
        # Assert
        self.assertEqual(result, expected_url)
        self.assertEqual(mock_blob.upload_from_string.call_count, 3)
        mock_blob.make_public.assert_called_once()
    
    def test_upload_with_permanent_failure(self):
        """Test upload with permanent failure that doesn't retry."""
        # Arrange
        test_case_id = 999
        screenshot_data = b"fake_screenshot_data"
        filename = "test_screenshot.png"
        
        # Mock blob that fails permanently
        mock_blob = Mock()
        mock_blob.upload_from_string.side_effect = GoogleCloudError("Permission denied")
        
        self.mock_bucket.blob.return_value = mock_blob
        
        # Act
        result = self.storage_service.upload_screenshot(test_case_id, screenshot_data, filename)
        
        # Assert
        self.assertIsNone(result)
        # Should not retry on permanent errors
        self.assertEqual(mock_blob.upload_from_string.call_count, 1)
        mock_blob.make_public.assert_not_called()
    
    def test_retry_backoff_calculation(self):
        """Test exponential backoff delay calculation with jitter."""
        # Test basic exponential backoff
        delay1 = _calculate_backoff_delay(0)
        delay2 = _calculate_backoff_delay(1)
        delay3 = _calculate_backoff_delay(2)
        
        # Should be approximately exponential
        self.assertGreater(delay2, delay1)
        self.assertGreater(delay3, delay2)
        
        # Should not exceed max delay
        self.assertLessEqual(delay1, 1.0)
        self.assertLessEqual(delay2, 1.0)
        self.assertLessEqual(delay3, 1.0)
        
        # Should be positive
        self.assertGreater(delay1, 0)
        self.assertGreater(delay2, 0)
        self.assertGreater(delay3, 0)
    
    def test_retry_decorator_with_success(self):
        """Test retry decorator with successful operation."""
        # Arrange
        mock_func = Mock(return_value="success")
        
        # Act
        decorated_func = retry_with_backoff(mock_func)
        result = decorated_func("arg1", kwarg1="value1")
        
        # Assert
        self.assertEqual(result, "success")
        mock_func.assert_called_once_with("arg1", kwarg1="value1")
    
    def test_retry_decorator_with_transient_failures(self):
        """Test retry decorator with transient failures."""
        # Arrange
        mock_func = Mock()
        mock_func.side_effect = [
            ServerError("Temporary error"),
            TooManyRequests("Rate limit"),
            "success"  # Success on third attempt
        ]
        
        # Act
        decorated_func = retry_with_backoff(mock_func)
        result = decorated_func()
        
        # Assert
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)
    
    def test_retry_decorator_with_max_attempts_exceeded(self):
        """Test retry decorator when max attempts are exceeded."""
        # Arrange
        mock_func = Mock()
        mock_func.side_effect = ServerError("Persistent error")
        
        # Act & Assert
        decorated_func = retry_with_backoff(mock_func)
        with self.assertRaises(ServerError):
            decorated_func()
        
        # Should have tried max_attempts times
        self.assertEqual(mock_func.call_count, 3)  # From env var GCS_RETRY_MAX_ATTEMPTS=3
    
    def test_cleanup_test_artifacts(self):
        """Test cleanup of test artifacts."""
        # Arrange
        test_case_id = 123
        
        # Mock blob listing
        mock_screenshot_blob = Mock()
        mock_video_blob = Mock()
        mock_log_blob = Mock()
        
        self.mock_client.list_blobs.side_effect = [
            [mock_screenshot_blob],  # screenshots
            [mock_video_blob],       # videos
            [mock_log_blob]          # logs
        ]
        
        # Act
        result = self.storage_service.cleanup_test_artifacts(test_case_id)
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(self.mock_client.list_blobs.call_count, 3)
        mock_screenshot_blob.delete.assert_called_once()
        mock_video_blob.delete.assert_called_once()
        mock_log_blob.delete.assert_called_once()
    
    def test_health_check(self):
        """Test storage service health check."""
        # Arrange
        self.mock_bucket.reload.return_value = None
        
        # Act
        health_status = self.storage_service.health_check()
        
        # Assert
        self.assertTrue(health_status["available"])
        self.assertTrue(health_status["bucket_configured"])
        self.assertTrue(health_status["client_initialized"])
        self.assertTrue(health_status["bucket_accessible"])
        self.assertEqual(health_status["bucket_name"], self.test_bucket_name)
        self.assertIn("retry_config", health_status)
    
    def test_health_check_with_bucket_error(self):
        """Test health check when bucket is not accessible."""
        # Arrange
        self.mock_bucket.reload.side_effect = GoogleCloudError("Bucket not found")
        
        # Act
        health_status = self.storage_service.health_check()
        
        # Assert
        self.assertFalse(health_status["bucket_accessible"])
        self.assertIn("error", health_status)
    
    def test_upload_multiple_artifact_types(self):
        """Test uploading multiple types of artifacts for a test case."""
        # Arrange
        test_case_id = 456
        screenshot_data = b"fake_screenshot"
        video_data = b"fake_video"
        logs_data = "fake logs content"
        
        # Mock blob operations
        mock_screenshot_blob = Mock()
        mock_screenshot_blob.public_url = "https://storage.googleapis.com/test-bucket/screenshots/456/screenshot.png"
        
        mock_video_blob = Mock()
        mock_video_blob.public_url = "https://storage.googleapis.com/test-bucket/videos/456/video.mp4"
        
        mock_logs_blob = Mock()
        mock_logs_blob.public_url = "https://storage.googleapis.com/test-bucket/logs/456/logs.txt"
        
        self.mock_bucket.blob.side_effect = [
            mock_screenshot_blob,
            mock_video_blob,
            mock_logs_blob
        ]
        
        # Act
        screenshot_url = self.storage_service.upload_screenshot(test_case_id, screenshot_data, "screenshot.png")
        video_url = self.storage_service.upload_video(test_case_id, video_data, "video.mp4")
        logs_url = self.storage_service.upload_logs(test_case_id, logs_data, "logs.txt")
        
        # Assert
        self.assertIsNotNone(screenshot_url)
        self.assertIsNotNone(video_url)
        self.assertIsNotNone(logs_url)
        
        self.assertEqual(self.mock_bucket.blob.call_count, 3)
        mock_screenshot_blob.upload_from_string.assert_called_once_with(screenshot_data)
        mock_video_blob.upload_from_string.assert_called_once_with(video_data)
        mock_logs_blob.upload_from_string.assert_called_once_with(logs_data.encode('utf-8'))
    
    def test_signed_url_generation(self):
        """Test signed URL generation with retry logic."""
        # Arrange
        file_path = "test/file.txt"
        expected_url = "https://storage.googleapis.com/test-bucket/test/file.txt?signature=abc123"
        
        mock_blob = Mock()
        mock_blob.generate_signed_url.return_value = expected_url
        self.mock_bucket.blob.return_value = mock_blob
        
        # Act
        result = self.storage_service.get_signed_url(file_path, expiration=3600)
        
        # Assert
        self.assertEqual(result, expected_url)
        mock_blob.generate_signed_url.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_blob.generate_signed_url.call_args
        self.assertEqual(call_args[1]["version"], "v4")
        self.assertEqual(call_args[1]["method"], "GET")
        self.assertIsInstance(call_args[1]["expiration"], datetime)
    
    def test_file_operations_with_retry(self):
        """Test file operations (download, delete) with retry logic."""
        # Arrange
        file_path = "test/file.txt"
        file_data = b"test file content"
        
        mock_blob = Mock()
        mock_blob.download_as_bytes.return_value = file_data
        self.mock_bucket.blob.return_value = mock_blob
        
        # Test download
        result = self.storage_service.download_file(file_path)
        self.assertEqual(result, file_data)
        
        # Test delete
        mock_blob.delete.return_value = None
        result = self.storage_service.delete_file(file_path)
        self.assertTrue(result)
        mock_blob.delete.assert_called_once()
    
    def test_storage_service_unavailable(self):
        """Test behavior when storage service is not available."""
        # Arrange - Create storage service without proper initialization
        with patch('app.services.storage_service.settings') as mock_settings:
            mock_settings.cloud_storage_bucket = None
            storage_service = StorageService()
        
        # Act & Assert
        self.assertFalse(storage_service.is_available())
        self.assertIsNone(storage_service.upload_bytes(b"data", "test.txt"))
        self.assertIsNone(storage_service.download_file("test.txt"))
        self.assertFalse(storage_service.delete_file("test.txt"))
        self.assertIsNone(storage_service.get_signed_url("test.txt"))


class TestStorageServiceIntegration(unittest.TestCase):
    """Integration tests for storage service with database and notification systems."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        # Similar setup as above but with more realistic mocking
        self.setup_mocks()
    
    def setup_mocks(self):
        """Set up all necessary mocks for integration testing."""
        # Mock environment and settings
        self.env_patcher = patch.dict(os.environ, {
            'GCS_RETRY_INITIAL_DELAY': '0.1',
            'GCS_RETRY_MAX_ATTEMPTS': '3'
        })
        self.env_patcher.start()
        
        # Mock Google Cloud Storage
        self.storage_patcher = patch('app.services.storage_service.storage.Client')
        self.mock_storage_client = self.storage_patcher.start()
        
        # Mock Slack service
        self.slack_patcher = patch('app.services.slack_service.slack_service')
        self.mock_slack = self.slack_patcher.start()
        
        # Mock database
        self.db_patcher = patch('app.services.persistence_service.Session')
        self.mock_db = self.db_patcher.start()
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        self.env_patcher.stop()
        self.storage_patcher.stop()
        self.slack_patcher.stop()
        self.db_patcher.stop()
    
    def test_complete_test_execution_flow(self):
        """Test complete flow from test execution to artifact storage and notification."""
        # This test would simulate the complete flow:
        # 1. Test execution generates artifacts
        # 2. Artifacts are uploaded to GCS
        # 3. Database is updated with URLs
        # 4. Notifications are sent
        
        # Implementation would depend on the actual execution flow
        # For now, this is a placeholder for the integration test
        pass


if __name__ == '__main__':
    unittest.main() 