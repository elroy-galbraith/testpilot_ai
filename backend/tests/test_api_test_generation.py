"""
Tests for test generation and execution API endpoints.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.models import TestCase, ExecutionResult
from app.auth.jwt_auth import jwt_auth


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def auth_token():
    """Create a valid JWT token for testing."""
    token_data = {
        "sub": "testuser",
        "email": "test@example.com",
        "permissions": ["test:generate", "test:execute", "test:read", "test:write"]
    }
    return jwt_auth.create_access_token(data=token_data)


@pytest.fixture
def auth_headers(auth_token):
    """Create authorization headers with JWT token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def mock_test_case():
    """Create a mock test case."""
    test_case = Mock(spec=TestCase)
    test_case.id = 1
    test_case.title = "Test Login Page"
    test_case.description = "Test login functionality"
    test_case.spec = "Create a login page with email and password fields"
    test_case.generated_code = "test('should login successfully', async ({ page }) => { await page.goto('/login'); });"
    test_case.framework = "playwright"
    test_case.language = "javascript"
    test_case.status = "generated"
    test_case.created_at = "2024-01-01T00:00:00Z"
    return test_case


@pytest.fixture
def mock_execution_result():
    """Create a mock execution result."""
    execution_result = Mock(spec=ExecutionResult)
    execution_result.id = 1
    execution_result.test_case_id = 1
    execution_result.status = "passed"
    execution_result.execution_time = 2.5
    execution_result.error_message = None
    execution_result.screenshot_path = "/screenshots/test.png"
    execution_result.video_path = None
    execution_result.logs = "Test passed successfully"
    execution_result.browser_info = {"browser": "chromium", "viewport": "1280x720"}
    execution_result.created_at = "2024-01-01T00:00:00Z"
    execution_result.meta_data = {"browser": "chromium", "headless": True}
    return execution_result


class TestAuthentication:
    """Test authentication endpoints."""
    
    def test_login_success(self, client):
        """Test successful login."""
        login_data = {
            "username": "testuser",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == "testuser"
        assert "test:generate" in data["permissions"]
    
    def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        response = client.post("/api/v1/auth/login", json={})
        
        assert response.status_code == 400
        assert "Username and password are required" in response.json()["detail"]
    
    def test_get_current_user_info(self, client, auth_headers):
        """Test getting current user information."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "test:generate" in data["permissions"]
    
    def test_get_current_user_info_unauthorized(self, client):
        """Test getting user info without authentication."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]


class TestTestGeneration:
    """Test test generation endpoints."""
    
    @patch('app.api.test_generation.agent_service')
    @patch('app.api.test_generation.get_test_case_repository')
    def test_generate_test_success(self, mock_repo_dep, mock_agent_service, client, auth_headers, mock_test_case):
        """Test successful test generation."""
        # Mock agent service response
        mock_agent_service.generate_test_cases.return_value = {
            "success": True,
            "test_cases": "test('should login successfully', async ({ page }) => { await page.goto('/login'); });",
            "model_used": "anthropic"
        }
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.create.return_value = mock_test_case
        mock_repo_dep.return_value = mock_repo
        
        # Test data
        generate_data = {
            "spec": "Create a login page with email and password fields",
            "framework": "playwright",
            "language": "javascript",
            "title": "Test Login Page",
            "description": "Test login functionality"
        }
        
        response = client.post("/api/v1/generate", json=generate_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["test_case_id"] == 1
        assert data["title"] == "Test Login Page"
        assert data["framework"] == "playwright"
        assert data["language"] == "javascript"
        assert data["status"] == "generated"
        assert "Test case generated successfully" in data["message"]
        
        # Verify service calls
        mock_agent_service.generate_test_cases.assert_called_once_with(
            specification=generate_data["spec"],
            framework=generate_data["framework"],
            language=generate_data["language"]
        )
        mock_repo.create.assert_called_once()
    
    @patch('app.api.test_generation.agent_service')
    def test_generate_test_agent_failure(self, mock_agent_service, client, auth_headers):
        """Test test generation when agent service fails."""
        # Mock agent service failure
        mock_agent_service.generate_test_cases.return_value = {
            "success": False,
            "error": "LLM service unavailable"
        }
        
        generate_data = {
            "spec": "Create a login page",
            "framework": "playwright"
        }
        
        response = client.post("/api/v1/generate", json=generate_data, headers=auth_headers)
        
        assert response.status_code == 500
        assert "Test generation failed" in response.json()["detail"]
    
    def test_generate_test_unauthorized(self, client):
        """Test test generation without authentication."""
        generate_data = {
            "spec": "Create a login page",
            "framework": "playwright"
        }
        
        response = client.post("/api/v1/generate", json=generate_data)
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_generate_test_invalid_spec(self, client, auth_headers):
        """Test test generation with invalid specification."""
        generate_data = {
            "spec": "short",  # Too short
            "framework": "playwright"
        }
        
        response = client.post("/api/v1/generate", json=generate_data, headers=auth_headers)
        
        assert response.status_code == 422  # Validation error


class TestTestExecution:
    """Test test execution endpoints."""
    
    @patch('app.api.test_generation.get_test_case_repository')
    @patch('app.api.test_generation.get_execution_repository')
    def test_execute_test_success(self, mock_execution_repo_dep, mock_test_case_repo_dep, client, auth_headers, mock_test_case, mock_execution_result):
        """Test successful test execution."""
        # Mock repositories
        mock_test_case_repo = Mock()
        mock_test_case_repo.get_by_id.return_value = mock_test_case
        
        mock_execution_repo = Mock()
        mock_execution_repo.create.return_value = mock_execution_result
        
        mock_test_case_repo_dep.return_value = mock_test_case_repo
        mock_execution_repo_dep.return_value = mock_execution_repo
        
        # Test data
        execute_data = {
            "test_case_id": 1,
            "browser": "chromium",
            "headless": True,
            "timeout": 30000
        }
        
        response = client.post("/api/v1/execute", json=execute_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["execution_id"] == 1
        assert data["test_case_id"] == 1
        assert data["status"] == "queued"
        assert data["job_id"] == "1"
        assert "Test execution has been queued" in data["message"]
        
        # Verify repository calls
        mock_test_case_repo.get_by_id.assert_called_once_with(1)
        mock_execution_repo.create.assert_called_once()
    
    @patch('app.api.test_generation.get_test_case_repository')
    def test_execute_test_not_found(self, mock_test_case_repo_dep, client, auth_headers):
        """Test execution with non-existent test case."""
        # Mock repository
        mock_test_case_repo = Mock()
        mock_test_case_repo.get_by_id.return_value = None
        
        mock_test_case_repo_dep.return_value = mock_test_case_repo
        
        execute_data = {
            "test_case_id": 999,
            "browser": "chromium"
        }
        
        response = client.post("/api/v1/execute", json=execute_data, headers=auth_headers)
        
        assert response.status_code == 404
        assert "Test case not found" in response.json()["detail"]
    
    @patch('app.api.test_generation.get_test_case_repository')
    def test_execute_test_no_code(self, mock_test_case_repo_dep, client, auth_headers):
        """Test execution with test case that has no generated code."""
        # Mock test case without generated code
        mock_test_case = Mock(spec=TestCase)
        mock_test_case.id = 1
        mock_test_case.generated_code = None
        
        mock_test_case_repo = Mock()
        mock_test_case_repo.get_by_id.return_value = mock_test_case
        
        mock_test_case_repo_dep.return_value = mock_test_case_repo
        
        execute_data = {
            "test_case_id": 1,
            "browser": "chromium"
        }
        
        response = client.post("/api/v1/execute", json=execute_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Test case has no generated code to execute" in response.json()["detail"]
    
    def test_execute_test_unauthorized(self, client):
        """Test test execution without authentication."""
        execute_data = {
            "test_case_id": 1,
            "browser": "chromium"
        }
        
        response = client.post("/api/v1/execute", json=execute_data)
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]


class TestExecutionResults:
    """Test execution results endpoints."""
    
    @patch('app.api.test_generation.get_execution_repository')
    def test_get_execution_results_success(self, mock_execution_repo_dep, client, auth_headers, mock_execution_result):
        """Test successful retrieval of execution results."""
        # Mock repository
        mock_execution_repo = Mock()
        mock_execution_repo.get_by_id.return_value = mock_execution_result
        
        mock_execution_repo_dep.return_value = mock_execution_repo
        
        response = client.get("/api/v1/results/1", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == 1
        assert data["test_case_id"] == 1
        assert data["status"] == "passed"
        assert data["execution_time"] == 2.5
        assert data["screenshot_path"] == "/screenshots/test.png"
        assert data["logs"] == "Test passed successfully"
        assert data["browser_info"]["browser"] == "chromium"
        
        # Verify repository call
        mock_execution_repo.get_by_id.assert_called_once_with(1)
    
    @patch('app.api.test_generation.get_execution_repository')
    def test_get_execution_results_not_found(self, mock_execution_repo_dep, client, auth_headers):
        """Test retrieval of non-existent execution results."""
        # Mock repository
        mock_execution_repo = Mock()
        mock_execution_repo.get_by_id.return_value = None
        
        mock_execution_repo_dep.return_value = mock_execution_repo
        
        response = client.get("/api/v1/results/999", headers=auth_headers)
        
        assert response.status_code == 404
        assert "Execution result not found" in response.json()["detail"]
    
    def test_get_execution_results_unauthorized(self, client):
        """Test getting execution results without authentication."""
        response = client.get("/api/v1/results/1")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]


class TestBackgroundExecution:
    """Test background execution functionality."""
    
    @patch('app.api.test_generation.execution_manager')
    @patch('app.api.test_generation.get_execution_repository')
    def test_execute_test_background_success(self, mock_execution_repo_dep, mock_execution_manager, mock_execution_result):
        """Test successful background execution."""
        # Mock execution manager result
        mock_result = Mock()
        mock_result.success = True
        mock_result.execution_time = 2.5
        mock_result.error_message = None
        mock_result.screenshot_path = "/screenshots/test.png"
        mock_result.console_logs = ["Test passed"]
        
        mock_execution_manager.execute_test = AsyncMock(return_value=mock_result)
        
        # Mock repository
        mock_execution_repo = Mock()
        mock_execution_repo.update.return_value = mock_execution_result
        
        mock_execution_repo_dep.return_value = mock_execution_repo
        
        # Mock test case
        mock_test_case = Mock()
        mock_test_case.id = 1
        mock_test_case.generated_code = "test code"
        
        # Mock execution result
        mock_execution_result = Mock()
        mock_execution_result.id = 1
        
        # Mock request
        mock_request = Mock()
        mock_request.browser = "chromium"
        mock_request.headless = True
        mock_request.timeout = 30000
        mock_request.retry_count = 3
        mock_request.retry_delay = 1000
        mock_request.viewport_width = 1280
        mock_request.viewport_height = 720
        mock_request.user_agent = None
        mock_request.screenshot_on_failure = True
        mock_request.capture_logs = True
        
        # Import and test the background function
        from app.api.test_generation import execute_test_background
        import asyncio
        
        # Run the background function
        asyncio.run(execute_test_background(
            mock_test_case,
            mock_execution_result,
            mock_request,
            mock_execution_repo
        ))
        
        # Verify calls
        mock_execution_repo.update.assert_called()
        mock_execution_manager.execute_test.assert_called_once()
    
    @patch('app.api.test_generation.execution_manager')
    @patch('app.api.test_generation.get_execution_repository')
    def test_execute_test_background_failure(self, mock_execution_repo_dep, mock_execution_manager, mock_execution_result):
        """Test background execution failure handling."""
        # Mock execution manager to raise exception
        mock_execution_manager.execute_test = AsyncMock(side_effect=Exception("Execution failed"))
        
        # Mock repository
        mock_execution_repo = Mock()
        mock_execution_repo.update.return_value = mock_execution_result
        
        mock_execution_repo_dep.return_value = mock_execution_repo
        
        # Mock test case
        mock_test_case = Mock()
        mock_test_case.id = 1
        mock_test_case.generated_code = "test code"
        
        # Mock execution result
        mock_execution_result = Mock()
        mock_execution_result.id = 1
        
        # Mock request
        mock_request = Mock()
        mock_request.browser = "chromium"
        mock_request.headless = True
        mock_request.timeout = 30000
        mock_request.retry_count = 3
        mock_request.retry_delay = 1000
        mock_request.viewport_width = 1280
        mock_request.viewport_height = 720
        mock_request.user_agent = None
        mock_request.screenshot_on_failure = True
        mock_request.capture_logs = True
        
        # Import and test the background function
        from app.api.test_generation import execute_test_background
        import asyncio
        
        # Run the background function
        asyncio.run(execute_test_background(
            mock_test_case,
            mock_execution_result,
            mock_request,
            mock_execution_repo
        ))
        
        # Verify error handling
        mock_execution_repo.update.assert_called()
        # Should be called with error status
        update_calls = mock_execution_repo.update.call_args_list
        assert any("error" in str(call) for call in update_calls)


class TestIntegration:
    """Integration tests for the complete workflow."""
    
    @patch('app.api.test_generation.agent_service')
    @patch('app.api.test_generation.get_test_case_repository')
    @patch('app.api.test_generation.get_execution_repository')
    def test_complete_workflow(self, mock_execution_repo_dep, mock_test_case_repo_dep, mock_agent_service, client, auth_headers, mock_test_case, mock_execution_result):
        """Test the complete workflow: generate -> execute -> get results."""
        # Mock agent service
        mock_agent_service.generate_test_cases.return_value = {
            "success": True,
            "test_cases": "test('should login successfully', async ({ page }) => { await page.goto('/login'); });",
            "model_used": "anthropic"
        }
        
        # Mock repositories
        mock_test_case_repo = Mock()
        mock_test_case_repo.get_by_id.return_value = mock_test_case
        mock_test_case_repo.create.return_value = mock_test_case
        
        mock_execution_repo = Mock()
        mock_execution_repo.create.return_value = mock_execution_result
        mock_execution_repo.get_by_id.return_value = mock_execution_result
        
        mock_test_case_repo_dep.return_value = mock_test_case_repo
        mock_execution_repo_dep.return_value = mock_execution_repo
        
        # Step 1: Generate test
        generate_data = {
            "spec": "Create a login page with email and password fields",
            "framework": "playwright",
            "language": "javascript",
            "title": "Test Login Page"
        }
        
        generate_response = client.post("/api/v1/generate", json=generate_data, headers=auth_headers)
        assert generate_response.status_code == 200
        test_case_id = generate_response.json()["test_case_id"]
        
        # Step 2: Execute test
        execute_data = {
            "test_case_id": test_case_id,
            "browser": "chromium",
            "headless": True
        }
        
        execute_response = client.post("/api/v1/execute", json=execute_data, headers=auth_headers)
        assert execute_response.status_code == 200
        execution_id = execute_response.json()["execution_id"]
        
        # Step 3: Get results
        results_response = client.get(f"/api/v1/results/{execution_id}", headers=auth_headers)
        assert results_response.status_code == 200
        results_data = results_response.json()
        assert results_data["execution_id"] == execution_id
        assert results_data["test_case_id"] == test_case_id
        
        # Verify all service calls were made
        mock_agent_service.generate_test_cases.assert_called_once()
        mock_test_case_repo.create.assert_called_once()
        mock_test_case_repo.get_by_id.assert_called_once_with(test_case_id)
        mock_execution_repo.create.assert_called_once()
        mock_execution_repo.get_by_id.assert_called_once_with(execution_id) 