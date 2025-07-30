"""
Tests for BackendAPIClient functionality.
"""

import pytest
import httpx
from unittest.mock import Mock, patch, AsyncMock
from app.services.backend_client import BackendAPIClient, retry_with_backoff
from app.config import settings


class TestRetryDecorator:
    """Test cases for the retry_with_backoff decorator."""
    
    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """Test that function succeeds on first attempt."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3)
        async def test_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await test_function()
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test that function succeeds after some failures."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.1)
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.TimeoutException("Timeout")
            return "success"
        
        result = await test_function()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_fails_after_max_attempts(self):
        """Test that function fails after max retry attempts."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.1)
        async def test_function():
            nonlocal call_count
            call_count += 1
            raise httpx.TimeoutException("Timeout")
        
        with pytest.raises(httpx.TimeoutException):
            await test_function()
        
        assert call_count == 3  # Initial attempt + 2 retries
    
    @pytest.mark.asyncio
    async def test_retry_does_not_retry_4xx_errors(self):
        """Test that 4xx errors are not retried."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3)
        async def test_function():
            nonlocal call_count
            call_count += 1
            raise httpx.HTTPStatusError("Bad Request", request=Mock(), response=Mock(status_code=400))
        
        with pytest.raises(httpx.HTTPStatusError):
            await test_function()
        
        assert call_count == 1  # No retries for 4xx errors
    
    @pytest.mark.asyncio
    async def test_retry_retries_5xx_errors(self):
        """Test that 5xx errors are retried."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.1)
        async def test_function():
            nonlocal call_count
            call_count += 1
            raise httpx.HTTPStatusError("Server Error", request=Mock(), response=Mock(status_code=500))
        
        with pytest.raises(httpx.HTTPStatusError):
            await test_function()
        
        assert call_count == 3  # Initial attempt + 2 retries


class TestBackendAPIClient:
    """Test cases for BackendAPIClient."""
    
    def test_client_initialization_with_valid_config(self):
        """Test client initialization with valid configuration."""
        with patch('app.services.backend_client.settings') as mock_settings:
            mock_settings.testpilot_api_url = "http://localhost:8000"
            mock_settings.testpilot_api_key = "test_key"
            mock_settings.testpilot_api_timeout = 60
            
            client = BackendAPIClient()
            assert client.base_url == "http://localhost:8000"
            assert client.api_key == "test_key"
            assert client.timeout == 60
    
    def test_client_initialization_without_api_url(self):
        """Test client initialization without API URL."""
        with patch('app.services.backend_client.settings') as mock_settings:
            mock_settings.testpilot_api_url = None
            mock_settings.testpilot_api_key = "test_key"
            mock_settings.testpilot_api_timeout = 60
            
            with pytest.raises(ValueError, match="TESTPILOT_API_URL is required"):
                BackendAPIClient()
    
    def test_get_default_headers_with_api_key(self):
        """Test default headers with API key."""
        with patch('app.services.backend_client.settings') as mock_settings:
            mock_settings.testpilot_api_url = "http://localhost:8000"
            mock_settings.testpilot_api_key = "test_key"
            mock_settings.testpilot_api_timeout = 60
            
            client = BackendAPIClient()
            headers = client._get_default_headers()
            
            assert headers["Content-Type"] == "application/json"
            assert headers["User-Agent"] == "TestPilot-Slack-Service/1.0"
            assert headers["Authorization"] == "Bearer test_key"
    
    def test_get_default_headers_without_api_key(self):
        """Test default headers without API key."""
        with patch('app.services.backend_client.settings') as mock_settings:
            mock_settings.testpilot_api_url = "http://localhost:8000"
            mock_settings.testpilot_api_key = None
            mock_settings.testpilot_api_timeout = 60
            
            client = BackendAPIClient()
            headers = client._get_default_headers()
            
            assert headers["Content-Type"] == "application/json"
            assert headers["User-Agent"] == "TestPilot-Slack-Service/1.0"
            assert "Authorization" not in headers
    
    def test_log_request_sanitizes_headers(self):
        """Test that request logging sanitizes sensitive headers."""
        with patch('app.services.backend_client.settings') as mock_settings:
            mock_settings.testpilot_api_url = "http://localhost:8000"
            mock_settings.testpilot_api_key = "test_key"
            mock_settings.testpilot_api_timeout = 60
            
            client = BackendAPIClient()
            
            with patch('app.services.backend_client.logger') as mock_logger:
                client._log_request("POST", "http://test.com", {"Authorization": "Bearer secret", "Content-Type": "application/json"})
                
                # Check that the log call was made
                mock_logger.debug.assert_called_once()
                log_call = mock_logger.debug.call_args[0][0]
                
                # Check that Authorization header was redacted
                assert "***REDACTED***" in log_call
                assert "Bearer secret" not in log_call
    
    def test_get_user_friendly_error_messages(self):
        """Test user-friendly error message generation."""
        with patch('app.services.backend_client.settings') as mock_settings:
            mock_settings.testpilot_api_url = "http://localhost:8000"
            mock_settings.testpilot_api_key = "test_key"
            mock_settings.testpilot_api_timeout = 60
            
            client = BackendAPIClient()
            
            # Test various error codes
            assert "Invalid request format" in client._get_user_friendly_error(400, "Bad Request")
            assert "Authentication failed" in client._get_user_friendly_error(401, "Unauthorized")
            assert "Access denied" in client._get_user_friendly_error(403, "Forbidden")
            assert "Resource not found" in client._get_user_friendly_error(404, "Not Found")
            assert "Rate limit exceeded" in client._get_user_friendly_error(429, "Too Many Requests")
            assert "Server error" in client._get_user_friendly_error(500, "Internal Server Error")
            assert "Unexpected error" in client._get_user_friendly_error(418, "I'm a teapot")


class TestBackendAPIClientMethods:
    """Test cases for BackendAPIClient API methods."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock BackendAPIClient."""
        with patch('app.services.backend_client.settings') as mock_settings:
            mock_settings.testpilot_api_url = "http://localhost:8000"
            mock_settings.testpilot_api_key = "test_key"
            mock_settings.testpilot_api_timeout = 60
            
            client = BackendAPIClient()
            client.client = AsyncMock()
            return client
    
    @pytest.mark.asyncio
    async def test_generate_test_case_success(self, mock_client):
        """Test successful test case generation."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test_case_id": 123, "code": "test code"}
        mock_response.text = '{"test_case_id": 123, "code": "test code"}'
        mock_response.headers = {}
        mock_response.request = Mock()
        
        mock_client.client.post.return_value = mock_response
        
        with patch.object(mock_client, '_log_request'), patch.object(mock_client, '_log_response'):
            result = await mock_client.generate_test_case("test spec")
            
            assert result == {"test_case_id": 123, "code": "test code"}
            mock_client.client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_test_case_http_error(self, mock_client):
        """Test test case generation with HTTP error."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.headers = {}
        mock_response.request = Mock()
        
        mock_client.client.post.return_value = mock_response
        
        with patch.object(mock_client, '_log_request'), patch.object(mock_client, '_log_response'):
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                await mock_client.generate_test_case("test spec")
            
            assert "Invalid request format" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_execute_test_success(self, mock_client):
        """Test successful test execution."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"execution_id": 456, "status": "queued"}
        mock_response.text = '{"execution_id": 456, "status": "queued"}'
        mock_response.headers = {}
        mock_response.request = Mock()
        
        mock_client.client.post.return_value = mock_response
        
        with patch.object(mock_client, '_log_request'), patch.object(mock_client, '_log_response'):
            result = await mock_client.execute_test(test_case_id=123)
            
            assert result == {"execution_id": 456, "status": "queued"}
            mock_client.client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_execution_results_success(self, mock_client):
        """Test successful execution results retrieval."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"execution_id": 456, "status": "completed", "result": "pass"}
        mock_response.text = '{"execution_id": 456, "status": "completed", "result": "pass"}'
        mock_response.headers = {}
        mock_response.request = Mock()
        
        mock_client.client.get.return_value = mock_response
        
        with patch.object(mock_client, '_log_request'), patch.object(mock_client, '_log_response'):
            result = await mock_client.get_execution_results(456)
            
            assert result == {"execution_id": 456, "status": "completed", "result": "pass"}
            mock_client.client.get.assert_called_once()


class TestBackendClientIntegration:
    """Integration tests for BackendAPIClient."""
    
    @pytest.mark.asyncio
    async def test_client_lifecycle(self):
        """Test client creation and cleanup."""
        with patch('app.services.backend_client.settings') as mock_settings:
            mock_settings.testpilot_api_url = "http://localhost:8000"
            mock_settings.testpilot_api_key = "test_key"
            mock_settings.testpilot_api_timeout = 60
            
            client = BackendAPIClient()
            assert client.client is not None
            
            # Test cleanup
            await client.close()
            # Note: In a real test, we'd verify the client was properly closed 