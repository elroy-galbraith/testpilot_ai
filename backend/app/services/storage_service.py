"""Storage service for GCP Cloud Storage operations."""

import os
import logging
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime, timedelta
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from app.config import settings
import hashlib

logger = logging.getLogger(__name__)

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
                except GoogleCloudError:
                    logger.warning(f"Bucket {settings.cloud_storage_bucket} not found. Artifact storage will be disabled.")
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
    
    def upload_file(self, file_data: BinaryIO, file_path: str, content_type: Optional[str] = None) -> Optional[str]:
        """Upload a file to Cloud Storage."""
        if not self.is_available():
            logger.warning("Cloud Storage not available. Cannot upload file.")
            return None
        
        try:
            blob = self.bucket.blob(file_path)
            
            # Set content type if provided
            if content_type:
                blob.content_type = content_type
            
            # Upload the file
            blob.upload_from_file(file_data)
            
            # Make the blob publicly readable (for screenshots and videos)
            blob.make_public()
            
            logger.info(f"File uploaded successfully: {file_path}")
            return blob.public_url
            
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {e}")
            return None
    
    def upload_bytes(self, data: bytes, file_path: str, content_type: Optional[str] = None) -> Optional[str]:
        """Upload bytes data to Cloud Storage."""
        if not self.is_available():
            logger.warning("Cloud Storage not available. Cannot upload data.")
            return None
        
        try:
            blob = self.bucket.blob(file_path)
            
            # Set content type if provided
            if content_type:
                blob.content_type = content_type
            
            # Upload the data
            blob.upload_from_string(data)
            
            # Make the blob publicly readable
            blob.make_public()
            
            logger.info(f"Data uploaded successfully: {file_path}")
            return blob.public_url
            
        except Exception as e:
            logger.error(f"Error uploading data to {file_path}: {e}")
            return None
    
    def download_file(self, file_path: str) -> Optional[bytes]:
        """Download a file from Cloud Storage."""
        if not self.is_available():
            logger.warning("Cloud Storage not available. Cannot download file.")
            return None
        
        try:
            blob = self.bucket.blob(file_path)
            return blob.download_as_bytes()
        except Exception as e:
            logger.error(f"Error downloading file {file_path}: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from Cloud Storage."""
        if not self.is_available():
            logger.warning("Cloud Storage not available. Cannot delete file.")
            return False
        
        try:
            blob = self.bucket.blob(file_path)
            blob.delete()
            logger.info(f"File deleted successfully: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in Cloud Storage."""
        if not self.is_available():
            return False
        
        try:
            blob = self.bucket.blob(file_path)
            return blob.exists()
        except Exception as e:
            logger.error(f"Error checking file existence {file_path}: {e}")
            return False
    
    def get_signed_url(self, file_path: str, expiration: int = 3600) -> Optional[str]:
        """Generate a signed URL for temporary access to a file."""
        if not self.is_available():
            logger.warning("Cloud Storage not available. Cannot generate signed URL.")
            return None
        
        try:
            blob = self.bucket.blob(file_path)
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.utcnow() + timedelta(seconds=expiration),
                method="GET"
            )
            return url
        except Exception as e:
            logger.error(f"Error generating signed URL for {file_path}: {e}")
            return None
    
    # TestPilot AI specific methods
    def upload_screenshot(self, test_case_id: int, screenshot_data: bytes, filename: str) -> Optional[str]:
        """Upload a test execution screenshot."""
        file_path = f"screenshots/{test_case_id}/{filename}"
        return self.upload_bytes(screenshot_data, file_path, "image/png")
    
    def upload_video(self, test_case_id: int, video_data: bytes, filename: str) -> Optional[str]:
        """Upload a test execution video."""
        file_path = f"videos/{test_case_id}/{filename}"
        return self.upload_bytes(video_data, file_path, "video/mp4")
    
    def upload_logs(self, test_case_id: int, logs_data: str, filename: str) -> Optional[str]:
        """Upload test execution logs."""
        file_path = f"logs/{test_case_id}/{filename}"
        return self.upload_bytes(logs_data.encode('utf-8'), file_path, "text/plain")
    
    def cleanup_test_artifacts(self, test_case_id: int) -> bool:
        """Clean up all artifacts for a test case."""
        if not self.is_available():
            return False
        
        try:
            # List all blobs with the test case prefix
            prefix = f"screenshots/{test_case_id}/"
            blobs = self.client.list_blobs(self.bucket, prefix=prefix)
            for blob in blobs:
                blob.delete()
            
            prefix = f"videos/{test_case_id}/"
            blobs = self.client.list_blobs(self.bucket, prefix=prefix)
            for blob in blobs:
                blob.delete()
            
            prefix = f"logs/{test_case_id}/"
            blobs = self.client.list_blobs(self.bucket, prefix=prefix)
            for blob in blobs:
                blob.delete()
            
            logger.info(f"Cleaned up artifacts for test case {test_case_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up artifacts for test case {test_case_id}: {e}")
            return False

# Global storage service instance
storage_service = StorageService() 