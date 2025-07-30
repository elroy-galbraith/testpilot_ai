"""
Tests for Slack integration functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.services.slack_service import SlackService
from app.config import settings


class TestSlackService:
    """Test cases for SlackService."""
    
    def test_slack_service_initialization_without_credentials(self):
        """Test Slack service initialization without credentials."""
        # Temporarily clear credentials
        original_signing_secret = settings.slack_signing_secret
        original_bot_token = settings.slack_bot_token
        
        try:
            settings.slack_signing_secret = None
            settings.slack_bot_token = None
            
            service = SlackService()
            assert not service.is_available()
            assert service.get_handler() is None
            
        finally:
            # Restore original values
            settings.slack_signing_secret = original_signing_secret
            settings.slack_bot_token = original_bot_token
    
    @patch('app.services.slack_service.App')
    def test_slack_service_initialization_with_credentials(self, mock_app_class):
        """Test Slack service initialization with credentials."""
        # Mock the App class
        mock_app = Mock()
        mock_app_class.return_value = mock_app
        
        # Set test credentials
        original_signing_secret = settings.slack_signing_secret
        original_bot_token = settings.slack_bot_token
        
        try:
            settings.slack_signing_secret = "test_signing_secret"
            settings.slack_bot_token = "xoxb-test_token"
            
            service = SlackService()
            
            # Verify App was called with correct parameters
            mock_app_class.assert_called_once_with(
                token="xoxb-test_token",
                signing_secret="test_signing_secret"
            )
            
        finally:
            # Restore original values
            settings.slack_signing_secret = original_signing_secret
            settings.slack_bot_token = original_bot_token
    
    @patch('app.services.slack_service.App')
    def test_slack_service_availability(self, mock_app_class):
        """Test Slack service availability check."""
        mock_app = Mock()
        mock_handler = Mock()
        mock_app_class.return_value = mock_app
        
        service = SlackService()
        
        # Mock the handler
        service.handler = mock_handler
        
        assert service.is_available()
        
        # Test when handler is None
        service.handler = None
        assert not service.is_available()


class TestSlackAPI:
    """Test cases for Slack API endpoints."""
    
    def test_slack_health_endpoint(self, client: TestClient):
        """Test Slack health endpoint."""
        response = client.get("/slack/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "slack_available" in data
        assert "credentials_configured" in data
        assert "handler_available" in data
    
    def test_slack_events_endpoint_without_config(self, client: TestClient):
        """Test Slack events endpoint without configuration."""
        # Temporarily clear credentials
        original_signing_secret = settings.slack_signing_secret
        original_bot_token = settings.slack_bot_token
        
        try:
            settings.slack_signing_secret = None
            settings.slack_bot_token = None
            
            # Test regular event (should return 503)
            response = client.post("/slack/events", json={})
            assert response.status_code == 503
            
            # Test challenge verification (should work even without config)
            challenge_response = client.post("/slack/events", content="challenge=test_challenge_value")
            assert challenge_response.status_code == 200
            assert challenge_response.text == "test_challenge_value"
            
        finally:
            # Restore original values
            settings.slack_signing_secret = original_signing_secret
            settings.slack_bot_token = original_bot_token
    
    def test_slack_challenge_verification(self, client: TestClient):
        """Test Slack URL verification challenge handling."""
        challenge_value = "test_challenge_12345"
        response = client.post("/slack/events", content=f"challenge={challenge_value}")
        
        assert response.status_code == 200
        assert response.text == challenge_value
        assert response.headers["content-type"] == "text/plain"
    
    def test_slack_events_get_endpoint(self, client: TestClient):
        """Test GET endpoint for basic connectivity."""
        response = client.get("/slack/events")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Slack events endpoint is active"
        assert data["status"] == "ok"
    
    @patch('app.services.slack_service.slack_service')
    def test_send_message_endpoint(self, mock_slack_service, client: TestClient):
        """Test send message endpoint."""
        mock_slack_service.is_available.return_value = True
        mock_slack_service.send_message = AsyncMock(return_value=True)
        
        response = client.post("/slack/send-message", json={
            "channel": "test-channel",
            "text": "Test message"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert data["channel"] == "test-channel"
    
    @patch('app.services.slack_service.slack_service')
    def test_send_rich_message_endpoint(self, mock_slack_service, client: TestClient):
        """Test send rich message endpoint."""
        mock_slack_service.is_available.return_value = True
        mock_slack_service.send_rich_message = AsyncMock(return_value=True)
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Test message"
                }
            }
        ]
        
        response = client.post("/slack/send-rich-message", json={
            "channel": "test-channel",
            "blocks": blocks
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert data["channel"] == "test-channel"


@pytest.fixture
def client():
    """Create a test client."""
    from main import app
    return TestClient(app) 