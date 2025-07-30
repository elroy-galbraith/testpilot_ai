"""
HTTP client wrapper for TestPilot AI backend API calls.
Handles authentication, error handling, and retry logic.
"""

import asyncio
import logging
import httpx
from typing import Optional, Dict, Any, Callable
from functools import wraps
from app.config import settings

logger = logging.getLogger(__name__)


def retry_with_backoff(max_retries: int = 3, base_delay: float = 0.5, max_delay: float = 10.0):
    """
    Decorator for retrying async functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(f"Final retry attempt failed for {func.__name__}: {e}")
                        raise
                    
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(f"Network error in {func.__name__} (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code >= 500:
                        last_exception = e
                        if attempt == max_retries:
                            logger.error(f"Final retry attempt failed for {func.__name__}: {e.response.status_code}")
                            raise
                        
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(f"Server error {e.response.status_code} in {func.__name__} (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay:.2f}s")
                        await asyncio.sleep(delay)
                    else:
                        # Don't retry 4xx errors
                        raise
            
            raise last_exception
        return wrapper
    return decorator


class BackendAPIClient:
    """HTTP client for TestPilot AI backend API calls."""
    
    def __init__(self):
        """Initialize the backend API client."""
        # Validate configuration first
        self._validate_config()
        
        self.base_url = settings.testpilot_api_url.rstrip('/')
        self.api_key = settings.testpilot_api_key
        self.timeout = settings.testpilot_api_timeout
        
        # Create HTTP client
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._get_default_headers()
        )
        
        logger.info(f"Backend API client initialized for {self.base_url}")
    
    def _validate_config(self):
        """Validate that required configuration is present."""
        if not settings.testpilot_api_url:
            raise ValueError("TESTPILOT_API_URL is required")
        
        if not settings.testpilot_api_key:
            logger.warning("TESTPILOT_API_KEY not provided - API calls may fail")
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "TestPilot-Slack-Service/1.0"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def _log_request(self, method: str, url: str, headers: Dict[str, str], payload: Optional[Dict] = None):
        """Log HTTP request details (sanitized)."""
        sanitized_headers = {k: v if k.lower() != 'authorization' else '***REDACTED***' for k, v in headers.items()}
        log_data = {
            "method": method,
            "url": url,
            "headers": sanitized_headers,
            "payload": payload
        }
        logger.debug(f"HTTP Request: {log_data}")
    
    def _log_response(self, status_code: int, headers: Dict[str, str], body: str):
        """Log HTTP response details."""
        log_data = {
            "status_code": status_code,
            "headers": dict(headers),
            "body": body[:500] + "..." if len(body) > 500 else body
        }
        logger.debug(f"HTTP Response: {log_data}")
    
    def _get_user_friendly_error(self, status_code: int, error_text: str) -> str:
        """Convert HTTP errors to user-friendly messages."""
        if status_code == 400:
            return "❌ Invalid request format. Please check your input and try again."
        elif status_code == 401:
            return "❌ Authentication failed. Please contact your administrator."
        elif status_code == 403:
            return "❌ Access denied. You don't have permission to perform this action."
        elif status_code == 404:
            return "❌ Resource not found. The requested test or endpoint doesn't exist."
        elif status_code == 429:
            return "⏳ Rate limit exceeded. Please wait a moment and try again."
        elif status_code >= 500:
            return "🔧 Server error. Our team has been notified. Please try again later."
        else:
            return f"❌ Unexpected error ({status_code}). Please try again or contact support."
    
    @retry_with_backoff(max_retries=3, base_delay=0.5, max_delay=10.0)
    async def generate_test_case(self, spec: str, framework: str = "playwright", 
                                language: str = "javascript", title: Optional[str] = None,
                                description: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Generate a test case using the backend API.
        
        Args:
            spec: Product specification for test generation
            framework: Testing framework (default: playwright)
            language: Programming language (default: javascript)
            title: Optional title for the test case
            description: Optional description for the test case
            
        Returns:
            Dict containing test case data or None if failed
        """
        payload = {
            "spec": spec,
            "framework": framework,
            "language": language
        }
        
        if title:
            payload["title"] = title
        if description:
            payload["description"] = description
        
        url = f"{self.base_url}/api/v1/generate"
        headers = self._get_default_headers()
        
        # Log request details
        self._log_request("POST", url, headers, payload)
        
        logger.info(f"Generating test case: {spec[:50]}...")
        response = await self.client.post(url, json=payload)
        
        # Log response details
        self._log_response(response.status_code, dict(response.headers), response.text)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Test case generated successfully: {result.get('test_case_id')}")
            return result
        else:
            error_message = self._get_user_friendly_error(response.status_code, response.text)
            logger.error(f"Failed to generate test case: {response.status_code} - {response.text}")
            raise httpx.HTTPStatusError(error_message, request=response.request, response=response)
    
    @retry_with_backoff(max_retries=3, base_delay=0.5, max_delay=10.0)
    async def execute_test(self, test_case_id: int, browser: str = "chromium",
                          headless: bool = True, timeout: int = 30000,
                          retry_count: int = 3, retry_delay: int = 1000,
                          screenshot_on_failure: bool = True,
                          capture_logs: bool = True) -> Optional[Dict[str, Any]]:
        """
        Execute a test case using the backend API.
        
        Args:
            test_case_id: ID of the test case to execute
            browser: Browser to use (default: chromium)
            headless: Run in headless mode (default: True)
            timeout: Test timeout in milliseconds (default: 30000)
            retry_count: Number of retry attempts (default: 3)
            retry_delay: Delay between retries in milliseconds (default: 1000)
            screenshot_on_failure: Capture screenshot on failure (default: True)
            capture_logs: Capture console and network logs (default: True)
            
        Returns:
            Dict containing execution result or None if failed
        """
        payload = {
            "test_case_id": test_case_id,
            "browser": browser,
            "headless": headless,
            "timeout": timeout,
            "retry_count": retry_count,
            "retry_delay": retry_delay,
            "screenshot_on_failure": screenshot_on_failure,
            "capture_logs": capture_logs
        }
        
        url = f"{self.base_url}/api/v1/execute"
        headers = self._get_default_headers()
        
        # Log request details
        self._log_request("POST", url, headers, payload)
        
        logger.info(f"Executing test case {test_case_id}")
        response = await self.client.post(url, json=payload)
        
        # Log response details
        self._log_response(response.status_code, dict(response.headers), response.text)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Test execution started: {result.get('execution_id')}")
            return result
        else:
            error_message = self._get_user_friendly_error(response.status_code, response.text)
            logger.error(f"Failed to execute test: {response.status_code} - {response.text}")
            raise httpx.HTTPStatusError(error_message, request=response.request, response=response)
    
    @retry_with_backoff(max_retries=3, base_delay=0.5, max_delay=10.0)
    async def get_execution_results(self, execution_id: int) -> Optional[Dict[str, Any]]:
        """
        Get execution results from the backend API.
        
        Args:
            execution_id: ID of the execution to get results for
            
        Returns:
            Dict containing execution results or None if failed
        """
        url = f"{self.base_url}/api/v1/results/{execution_id}"
        headers = self._get_default_headers()
        
        # Log request details
        self._log_request("GET", url, headers)
        
        logger.info(f"Getting execution results for {execution_id}")
        response = await self.client.get(url)
        
        # Log response details
        self._log_response(response.status_code, dict(response.headers), response.text)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Retrieved execution results for {execution_id}")
            return result
        else:
            error_message = self._get_user_friendly_error(response.status_code, response.text)
            logger.error(f"Failed to get execution results: {response.status_code} - {response.text}")
            raise httpx.HTTPStatusError(error_message, request=response.request, response=response)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("Backend API client closed")


# Global backend client instance
backend_client: Optional[BackendAPIClient] = None


async def get_backend_client() -> BackendAPIClient:
    """Get the global backend client instance."""
    global backend_client
    if backend_client is None:
        backend_client = BackendAPIClient()
    return backend_client


async def close_backend_client():
    """Close the global backend client instance."""
    global backend_client
    if backend_client:
        await backend_client.close()
        backend_client = None 