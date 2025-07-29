"""Storage service for GCP Cloud Storage operations."""

import logging
from typing import Optional, BinaryIO, Dict, Any
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
from google.cloud.exceptions import GoogleCloudError
import os

from app.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    """Service for handling GCP Cloud Storage operations."""
    
    def __init__(self):
        """Initialize the StorageService with GCP Cloud Storage client."""
        self.client = None
        self.bucket = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the GCP Cloud Storage client."""
        try:
            # Check if we have a service account key file
            if settings.gcp_service_account_key_path and os.path.exists(settings.gcp_service_account_key_path):
                self.client = storage.Client.from_service_account_json(
                    settings.gcp_service_account_key_path
                )
                logger.info("Initialized GCP Cloud Storage client with service account key")
            else:
                # Try to use default credentials (for Cloud Run, GCE, etc.)
                self.client = storage.Client()
                logger.info("Initialized GCP Cloud Storage client with default credentials")
            
            # Get the bucket
            if settings.cloud_storage_bucket:
                self.bucket = self.client.bucket(settings.cloud_storage_bucket)
                logger.info(f"Connected to Cloud Storage bucket: {settings.cloud_storage_bucket}")
            else:
                logger.warning("No Cloud Storage bucket configured")
                
        except DefaultCredentialsError:
            logger.error("Failed to initialize GCP Cloud Storage client: No credentials found")
            self.client = None
            self.bucket = None
        except GoogleCloudError as e:
            logger.error(f"Failed to initialize GCP Cloud Storage client: {e}")
            self.client = None
            self.bucket = None
    
    def upload_file(self, file_path: str, destination_blob_name: str) -> Optional[str]:
        """
        Upload a file to Cloud Storage.
        
        Args:
            file_path: Local path to the file
            destination_blob_name: Name for the blob in Cloud Storage
            
        Returns:
            Public URL of the uploaded file or None if failed
        """
        if not self.bucket:
            logger.error("No Cloud Storage bucket configured")
            return None
        
        try:
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(file_path)
            
            # Make the blob publicly readable
            blob.make_public()
            
            logger.info(f"Uploaded {file_path} to {destination_blob_name}")
            return blob.public_url
            
        except GoogleCloudError as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            return None
    
    def upload_bytes(self, data: bytes, destination_blob_name: str, content_type: str = None) -> Optional[str]:
        """
        Upload bytes data to Cloud Storage.
        
        Args:
            data: Bytes data to upload
            destination_blob_name: Name for the blob in Cloud Storage
            content_type: MIME type of the data
            
        Returns:
            Public URL of the uploaded file or None if failed
        """
        if not self.bucket:
            logger.error("No Cloud Storage bucket configured")
            return None
        
        try:
            blob = self.bucket.blob(destination_blob_name)
            
            if content_type:
                blob.content_type = content_type
            
            blob.upload_from_string(data)
            
            # Make the blob publicly readable
            blob.make_public()
            
            logger.info(f"Uploaded bytes to {destination_blob_name}")
            return blob.public_url
            
        except GoogleCloudError as e:
            logger.error(f"Failed to upload bytes to {destination_blob_name}: {e}")
            return None
    
    def download_file(self, source_blob_name: str, destination_file_path: str) -> bool:
        """
        Download a file from Cloud Storage.
        
        Args:
            source_blob_name: Name of the blob in Cloud Storage
            destination_file_path: Local path where to save the file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.bucket:
            logger.error("No Cloud Storage bucket configured")
            return False
        
        try:
            blob = self.bucket.blob(source_blob_name)
            blob.download_to_filename(destination_file_path)
            
            logger.info(f"Downloaded {source_blob_name} to {destination_file_path}")
            return True
            
        except GoogleCloudError as e:
            logger.error(f"Failed to download {source_blob_name}: {e}")
            return False
    
    def delete_file(self, blob_name: str) -> bool:
        """
        Delete a file from Cloud Storage.
        
        Args:
            blob_name: Name of the blob to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.bucket:
            logger.error("No Cloud Storage bucket configured")
            return False
        
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            
            logger.info(f"Deleted {blob_name} from Cloud Storage")
            return True
            
        except GoogleCloudError as e:
            logger.error(f"Failed to delete {blob_name}: {e}")
            return False
    
    def get_file_url(self, blob_name: str) -> Optional[str]:
        """
        Get the public URL of a file in Cloud Storage.
        
        Args:
            blob_name: Name of the blob
            
        Returns:
            Public URL or None if not found
        """
        if not self.bucket:
            logger.error("No Cloud Storage bucket configured")
            return None
        
        try:
            blob = self.bucket.blob(blob_name)
            if blob.exists():
                return blob.public_url
            else:
                logger.warning(f"Blob {blob_name} does not exist")
                return None
                
        except GoogleCloudError as e:
            logger.error(f"Failed to get URL for {blob_name}: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the storage service.
        
        Returns:
            Dictionary with health status information
        """
        if not self.client:
            return {
                "available": False,
                "configured": False,
                "error": "No GCP Cloud Storage client available"
            }
        
        if not self.bucket:
            return {
                "available": False,
                "configured": False,
                "error": "No Cloud Storage bucket configured"
            }
        
        try:
            # Test bucket access
            self.bucket.reload()
            return {
                "available": True,
                "configured": True,
                "bucket": settings.cloud_storage_bucket,
                "project": settings.gcp_project_id
            }
            
        except GoogleCloudError as e:
            return {
                "available": False,
                "configured": True,
                "error": str(e)
            } 