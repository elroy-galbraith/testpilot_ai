"""Storage service for GCP Cloud Storage operations."""

import os
import logging
import time
import random
import functools
from typing import Optional, Dict, Any, BinaryIO, Callable
from datetime import datetime, timedelta
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError, ServerError, TooManyRequests
from google.api_core import retry as google_retry
from app.config import settings
import hashlib

logger = logging.getLogger(__name__)

# Retry configuration
RETRY_CONFIG = {
    "initial_delay": float(os.getenv("GCS_RETRY_INITIAL_DELAY", "0.2")),  # 200ms
    "multiplier": float(os.getenv("GCS_RETRY_MULTIPLIER", "2.0")),
    "max_delay": float(os.getenv("GCS_RETRY_MAX_DELAY", "5.0")),  # 5 seconds
    "max_attempts": int(os.getenv("GCS_RETRY_MAX_ATTEMPTS", "5")),
    "jitter": float(os.getenv("GCS_RETRY_JITTER", "0.1"))  # 10% jitter
}

def retry_with_backoff(func: Callable) -> Callable:
    """Decorator to add exponential backoff retry logic to GCS operations."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        last_exception = None
        
        for attempt in range(RETRY_CONFIG["max_attempts"]):
            try:
                return func(*args, **kwargs)
            except (ServerError, TooManyRequests) as e:
                # These are transient errors that should be retried
                last_exception = e
                if attempt < RETRY_CONFIG["max_attempts"] - 1:
                    delay = _calculate_backoff_delay(attempt)
                    logger.warning(
                        f"GCS operation failed (attempt {attempt + 1}/{RETRY_CONFIG['max_attempts']}): "
                        f"Error: {type(e).__name__}: {str(e)}, "
                        f"Retrying in {delay:.2f}s"
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"GCS operation failed after {RETRY_CONFIG['max_attempts']} attempts: "
                        f"Error: {type(e).__name__}: {str(e)}"
                    )
                    raise
            except GoogleCloudError as e:
                # Non-transient errors, don't retry
                logger.error(f"GCS operation failed with non-transient error: {type(e).__name__}: {str(e)}")
                raise
            except Exception as e:
                # Unexpected errors, log and re-raise
                logger.error(f"Unexpected error in GCS operation: {type(e).__name__}: {str(e)}")
                raise
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
    
    return wrapper

def _calculate_backoff_delay(attempt: int) -> float:
    """Calculate exponential backoff delay with jitter."""
    delay = RETRY_CONFIG["initial_delay"] * (RETRY_CONFIG["multiplier"] ** attempt)
    delay = min(delay, RETRY_CONFIG["max_delay"])
    
    # Add jitter to prevent thundering herd
    jitter_amount = delay * RETRY_CONFIG["jitter"]
    delay += random.uniform(-jitter_amount, jitter_amount)
    
    return max(0, delay)

class StorageService:
    """GCP Cloud Storage service for TestPilot AI artifacts."""
    
    def __init__(self):
        self.client = None
        self.bucket = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize GCP Cloud Storage client."""
        try:
            # Initialize the client
            if settings.gcp_service_account_key_path and os.path.exists(settings.gcp_service_account_key_path):
                # Use service account key file for local development
                self.client = storage.Client.from_service_account_json(
                    settings.gcp_service_account_key_path
                )
            else:
                # Use default credentials (for GCP deployment)
                self.client = storage.Client()
            
            # Get or create bucket
            if settings.cloud_storage_bucket:
                try:
                    self.bucket = self.client.bucket(settings.cloud_storage_bucket)
                    # Test if bucket exists
                    self.bucket.reload()
                    logger.info(f"Connected to GCP Cloud Storage bucket: {settings.cloud_storage_bucket}")
                except GoogleCloudError as e:
                    logger.warning(f"Bucket {settings.cloud_storage_bucket} not found. Artifact storage will be disabled. Error: {e}")
                    self.bucket = None
            else:
                logger.warning("No Cloud Storage bucket configured. Artifact storage will be disabled.")
                self.bucket = None
                
        except Exception as e:
            logger.warning(f"Failed to initialize GCP Cloud Storage: {e}. Artifact storage will be disabled.")
            self.client = None
            self.bucket = None
    
    def is_available(self) -> bool:
        """Check if Cloud Storage is available."""
        return self.client is not None and self.bucket is not None
    
    @retry_with_backoff
    def _upload_blob_with_retry(self, blob, data: bytes, content_type: Optional[str] = None) -> str:
        """Upload data to a blob with retry logic."""
        if content_type:
            blob.content_type = content_type
        
        blob.upload_from_string(data)
        blob.make_public()
        return blob.public_url
    
    @retry_with_backoff
    def _upload_file_with_retry(self, blob, file_data: BinaryIO, content_type: Optional[str] = None) -> str:
        """Upload file to a blob with retry logic."""
        if content_type:
            blob.content_type = content_type
        
        blob.upload_from_file(file_data)
        blob.make_public()
        return blob.public_url
    
    def upload_file(self, file_data: BinaryIO, file_path: str, content_type: Optional[str] = None) -> Optional[str]:
        """Upload a file to Cloud Storage with retry logic and detailed logging."""
        if not self.is_available():
            logger.warning("Cloud Storage not available. Cannot upload file.")
            return None
        
        try:
            logger.info(f"Starting file upload to GCS: {file_path}")
            blob = self.bucket.blob(file_path)
            
            url = self._upload_file_with_retry(blob, file_data, content_type)
            
            logger.info(f"File uploaded successfully to GCS: {file_path} -> {url}")
            return url
            
        except Exception as e:
            logger.error(
                f"Failed to upload file to GCS after all retries: {file_path}, "
                f"Error: {type(e).__name__}: {str(e)}, "
                f"Bucket: {settings.cloud_storage_bucket}"
            )
            return None
    
    def upload_bytes(self, data: bytes, file_path: str, content_type: Optional[str] = None) -> Optional[str]:
        """Upload bytes data to Cloud Storage with retry logic and detailed logging."""
        if not self.is_available():
            logger.warning("Cloud Storage not available. Cannot upload data.")
            return None
        
        try:
            logger.info(f"Starting data upload to GCS: {file_path} (size: {len(data)} bytes)")
            blob = self.bucket.blob(file_path)
            
            url = self._upload_blob_with_retry(blob, data, content_type)
            
            logger.info(f"Data uploaded successfully to GCS: {file_path} -> {url}")
            return url
            
        except Exception as e:
            logger.error(
                f"Failed to upload data to GCS after all retries: {file_path}, "
                f"Error: {type(e).__name__}: {str(e)}, "
                f"Bucket: {settings.cloud_storage_bucket}, "
                f"Data size: {len(data)} bytes"
            )
            return None
    
    @retry_with_backoff
    def download_file(self, file_path: str) -> Optional[bytes]:
        """Download a file from Cloud Storage with retry logic."""
        if not self.is_available():
            logger.warning("Cloud Storage not available. Cannot download file.")
            return None
        
        try:
            logger.info(f"Downloading file from GCS: {file_path}")
            blob = self.bucket.blob(file_path)
            data = blob.download_as_bytes()
            logger.info(f"File downloaded successfully from GCS: {file_path} (size: {len(data)} bytes)")
            return data
        except Exception as e:
            logger.error(f"Failed to download file from GCS: {file_path}, Error: {type(e).__name__}: {str(e)}")
            return None
    
    @retry_with_backoff
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from Cloud Storage with retry logic."""
        if not self.is_available():
            logger.warning("Cloud Storage not available. Cannot delete file.")
            return False
        
        try:
            logger.info(f"Deleting file from GCS: {file_path}")
            blob = self.bucket.blob(file_path)
            blob.delete()
            logger.info(f"File deleted successfully from GCS: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from GCS: {file_path}, Error: {type(e).__name__}: {str(e)}")
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in Cloud Storage."""
        if not self.is_available():
            return False
        
        try:
            blob = self.bucket.blob(file_path)
            exists = blob.exists()
            logger.debug(f"File existence check for GCS: {file_path} -> {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking file existence in GCS: {file_path}, Error: {type(e).__name__}: {str(e)}")
            return False
    
    @retry_with_backoff
    def get_signed_url(self, file_path: str, expiration: int = 3600) -> Optional[str]:
        """Generate a signed URL for temporary access to a file with retry logic."""
        if not self.is_available():
            logger.warning("Cloud Storage not available. Cannot generate signed URL.")
            return None
        
        try:
            logger.info(f"Generating signed URL for GCS file: {file_path} (expiration: {expiration}s)")
            blob = self.bucket.blob(file_path)
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.utcnow() + timedelta(seconds=expiration),
                method="GET"
            )
            logger.info(f"Signed URL generated successfully for GCS: {file_path}")
            return url
        except Exception as e:
            logger.error(f"Failed to generate signed URL for GCS: {file_path}, Error: {type(e).__name__}: {str(e)}")
            return None
    
    # TestPilot AI specific methods with enhanced logging
    def upload_screenshot(self, test_case_id: int, screenshot_data: bytes, filename: str) -> Optional[str]:
        """Upload a test execution screenshot with enhanced logging."""
        file_path = f"screenshots/{test_case_id}/{filename}"
        logger.info(f"Uploading screenshot for test case {test_case_id}: {filename}")
        
        url = self.upload_bytes(screenshot_data, file_path, "image/png")
        
        if url:
            logger.info(f"Screenshot uploaded successfully for test case {test_case_id}: {url}")
        else:
            logger.error(f"Failed to upload screenshot for test case {test_case_id}: {filename}")
        
        return url
    
    def upload_video(self, test_case_id: int, video_data: bytes, filename: str) -> Optional[str]:
        """Upload a test execution video with enhanced logging."""
        file_path = f"videos/{test_case_id}/{filename}"
        logger.info(f"Uploading video for test case {test_case_id}: {filename}")
        
        url = self.upload_bytes(video_data, file_path, "video/mp4")
        
        if url:
            logger.info(f"Video uploaded successfully for test case {test_case_id}: {url}")
        else:
            logger.error(f"Failed to upload video for test case {test_case_id}: {filename}")
        
        return url
    
    def upload_logs(self, test_case_id: int, logs_data: str, filename: str) -> Optional[str]:
        """Upload test execution logs with enhanced logging."""
        file_path = f"logs/{test_case_id}/{filename}"
        logger.info(f"Uploading logs for test case {test_case_id}: {filename}")
        
        url = self.upload_bytes(logs_data.encode('utf-8'), file_path, "text/plain")
        
        if url:
            logger.info(f"Logs uploaded successfully for test case {test_case_id}: {url}")
        else:
            logger.error(f"Failed to upload logs for test case {test_case_id}: {filename}")
        
        return url
    
    def cleanup_test_artifacts(self, test_case_id: int) -> bool:
        """Clean up all artifacts for a test case with enhanced logging."""
        if not self.is_available():
            logger.warning(f"Cloud Storage not available. Cannot cleanup artifacts for test case {test_case_id}")
            return False
        
        try:
            logger.info(f"Starting cleanup of artifacts for test case {test_case_id}")
            
            # List all blobs with the test case prefix
            prefix = f"screenshots/{test_case_id}/"
            blobs = self.client.list_blobs(self.bucket, prefix=prefix)
            screenshot_count = 0
            for blob in blobs:
                blob.delete()
                screenshot_count += 1
            
            prefix = f"videos/{test_case_id}/"
            blobs = self.client.list_blobs(self.bucket, prefix=prefix)
            video_count = 0
            for blob in blobs:
                blob.delete()
                video_count += 1
            
            prefix = f"logs/{test_case_id}/"
            blobs = self.client.list_blobs(self.bucket, prefix=prefix)
            log_count = 0
            for blob in blobs:
                blob.delete()
                log_count += 1
            
            logger.info(f"Cleaned up artifacts for test case {test_case_id}: "
                       f"{screenshot_count} screenshots, {video_count} videos, {log_count} logs")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up artifacts for test case {test_case_id}: {type(e).__name__}: {str(e)}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the storage service."""
        health_status = {
            "available": self.is_available(),
            "bucket_configured": bool(settings.cloud_storage_bucket),
            "client_initialized": self.client is not None,
            "bucket_accessible": False,
            "retry_config": RETRY_CONFIG
        }
        
        if self.is_available():
            try:
                # Test bucket accessibility
                self.bucket.reload()
                health_status["bucket_accessible"] = True
                health_status["bucket_name"] = settings.cloud_storage_bucket
            except Exception as e:
                health_status["error"] = str(e)
        
        return health_status

# Global storage service instance
storage_service = StorageService() 