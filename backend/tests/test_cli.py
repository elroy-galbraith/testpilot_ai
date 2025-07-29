"""
Unit tests for TestPilot CLI tool.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from testpilot_cli import cli, load_specification, save_output, generate, health, config, playwright


class TestCLIHelpers:
    """Test helper functions for the CLI."""
    
    def test_load_specification_from_file(self):
        """Test loading specification from a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test specification content")
            temp_file = f.name
        
        try:
            result = load_specification(temp_file)
            assert result == "Test specification content"
        finally:
            os.unlink(temp_file)
    
    def test_load_specification_from_string(self):
        """Test loading specification from a string."""
        spec_text = "User should be able to login"
        result = load_specification(spec_text)
        assert result == spec_text
    
    def test_save_output_to_file(self):
        """Test saving output to a file."""
        output_data = {"success": True, "test_cases": "test content"}
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_file = f.name
        
        try:
            save_output(output_data, temp_file)
            
            with open(temp_file, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data == output_data
        finally:
            os.unlink(temp_file)
    
    def test_save_output_to_stdout(self, capsys):
        """Test saving output to stdout."""
        output_data = {"success": True, "test_cases": "test content"}
        save_output(output_data)
        
        captured = capsys.readouterr()
        assert json.loads(captured.out) == output_data


class TestCLICommands:
    """Test CLI commands."""
    
    @patch('testpilot_cli.AgentService')
    def test_config_command(self, mock_agent_service_class):
        """Test the config command."""
        
        # Mock settings
        with patch('testpilot_cli.settings') as mock_settings:
            mock_settings.openai_api_key = "test_openai_key"
            mock_settings.anthropic_api_key = "your_anthropic_api_key_here"
            mock_settings.debug = True
            mock_settings.host = "0.0.0.0"
            mock_settings.port = 8000
            mock_settings.database_url = "sqlite:///test.db"
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.gcp_project_id = "test-project"
            
            # Mock click.echo and sys.exit
            with patch('testpilot_cli.click.echo') as mock_echo, \
                 patch('testpilot_cli.sys.exit') as mock_exit:
                config()
                
                # Verify that click.echo was called with JSON config
                mock_echo.assert_called()
                call_args = mock_echo.call_args_list
                
                # Check that config info was printed
                config_call = call_args[0]
                config_text = config_call[0][0]
                config_data = json.loads(config_text)
                
                assert config_data["openai_configured"] is True
                assert config_data["anthropic_configured"] is False
                assert config_data["debug"] is True
                assert config_data["host"] == "0.0.0.0"
                assert config_data["port"] == 8000
    
    @patch('testpilot_cli.AgentService')
    def test_health_command_success(self, mock_agent_service_class):
        """Test the health command when service is healthy."""
        
        # Mock AgentService instance
        mock_agent_service = Mock()
        mock_agent_service_class.return_value = mock_agent_service
        
        # Mock health check response
        mock_agent_service.health_check.return_value = {
            "openai": {"available": True, "configured": True},
            "anthropic": {"available": False, "configured": False},
            "test_query": True
        }
        
        # Mock click.echo and sys.exit
        with patch('testpilot_cli.click.echo') as mock_echo, \
             patch('testpilot_cli.sys.exit') as mock_exit:
            
            health()
            
            # Verify success message
            mock_echo.assert_any_call("✅ TestPilot service is healthy")
            mock_echo.assert_any_call("Available providers: OpenAI")
            mock_echo.assert_any_call("Test query: ✅ Success")
            mock_exit.assert_called_with(0)
    
    @patch('testpilot_cli.AgentService')
    def test_health_command_failure(self, mock_agent_service_class):
        """Test the health command when service is unhealthy."""
        
        # Mock AgentService instance
        mock_agent_service = Mock()
        mock_agent_service_class.return_value = mock_agent_service
        
        # Mock health check response indicating failure
        mock_agent_service.health_check.return_value = {
            "openai": {"available": False, "configured": False},
            "anthropic": {"available": False, "configured": False},
            "test_query": False
        }
        
        # Mock click.echo and sys.exit
        with patch('testpilot_cli.click.echo') as mock_echo, \
             patch('testpilot_cli.sys.exit') as mock_exit:
            
            health()
            
            # Verify failure message
            mock_echo.assert_any_call("❌ TestPilot service is unhealthy", err=True)
            mock_echo.assert_any_call("No LLM providers are available", err=True)
            mock_exit.assert_called_with(1)
    
    @patch('testpilot_cli.AgentService')
    def test_generate_command_playwright(self, mock_agent_service_class):
        """Test the generate command with playwright format."""
        
        # Mock AgentService instance
        mock_agent_service = Mock()
        mock_agent_service_class.return_value = mock_agent_service
        
        # Mock successful response
        mock_agent_service.generate_test_cases.return_value = {
            "success": True,
            "test_cases": "Generated test cases",
            "framework": "playwright",
            "language": "javascript",
            "model_used": "openai"
        }
        
        # Mock click.echo and sys.exit
        with patch('testpilot_cli.click.echo') as mock_echo, \
             patch('testpilot_cli.sys.exit') as mock_exit:
            
            generate("Test specification", "playwright", "javascript", None, "http://localhost:3000")
            
            # Verify AgentService was called correctly
            mock_agent_service.generate_test_cases.assert_called_with(
                specification="Test specification",
                framework="playwright",
                language="javascript"
            )
            
            # Verify output was printed
            mock_echo.assert_called()
            mock_exit.assert_called_with(0)
    
    @patch('testpilot_cli.AgentService')
    def test_generate_command_english(self, mock_agent_service_class):
        """Test the generate command with english format."""
        
        # Mock AgentService instance
        mock_agent_service = Mock()
        mock_agent_service_class.return_value = mock_agent_service
        
        # Mock successful response
        mock_agent_service.generate_english_description.return_value = {
            "success": True,
            "description": "English description",
            "model_used": "openai"
        }
        
        # Mock click.echo and sys.exit
        with patch('testpilot_cli.click.echo') as mock_echo, \
             patch('testpilot_cli.sys.exit') as mock_exit:
            
            generate("Test specification", "english", "javascript", None, "http://localhost:3000")
            
            # Verify AgentService was called correctly
            mock_agent_service.generate_english_description.assert_called_with("Test specification")
            
            # Verify output was printed
            mock_echo.assert_called()
            mock_exit.assert_called_with(0)
    
    @patch('testpilot_cli.AgentService')
    def test_generate_command_failure(self, mock_agent_service_class):
        """Test the generate command when AgentService fails."""
        
        # Mock AgentService instance
        mock_agent_service = Mock()
        mock_agent_service_class.return_value = mock_agent_service
        
        # Mock failed response
        mock_agent_service.generate_test_cases.return_value = {
            "success": False,
            "error": "API error occurred"
        }
        
        # Mock click.echo and sys.exit
        with patch('testpilot_cli.click.echo') as mock_echo, \
             patch('testpilot_cli.sys.exit') as mock_exit:
            
            generate("Test specification", "playwright", "javascript", None, "http://localhost:3000")
            
            # Verify error message was printed
            mock_echo.assert_any_call("Error generating test cases: API error occurred", err=True)
            mock_exit.assert_called_with(1)
    
    @patch('testpilot_cli.AgentService')
    def test_playwright_command(self, mock_agent_service_class):
        """Test the playwright command."""
        
        # Mock AgentService instance
        mock_agent_service = Mock()
        mock_agent_service_class.return_value = mock_agent_service
        
        # Mock successful response
        mock_agent_service.generate_playwright_script.return_value = {
            "success": True,
            "script": "Generated Playwright script",
            "base_url": "https://example.com",
            "model_used": "openai"
        }
        
        # Mock click.echo and sys.exit
        with patch('testpilot_cli.click.echo') as mock_echo, \
             patch('testpilot_cli.sys.exit') as mock_exit:
            
            playwright("Test case description", "https://example.com", None)
            
            # Verify AgentService was called correctly
            mock_agent_service.generate_playwright_script.assert_called_with(
                test_case="Test case description",
                base_url="https://example.com"
            )
            
            # Verify output was printed
            mock_echo.assert_called()
            mock_exit.assert_called_with(0)


class TestCLIErrorHandling:
    """Test CLI error handling."""
    
    @patch('testpilot_cli.AgentService')
    def test_agent_service_initialization_error(self, mock_agent_service_class):
        """Test handling of AgentService initialization errors."""
        
        # Mock AgentService to raise an exception
        mock_agent_service_class.side_effect = Exception("Service initialization failed")
        
        # Mock click.echo and sys.exit
        with patch('testpilot_cli.click.echo') as mock_echo, \
             patch('testpilot_cli.sys.exit') as mock_exit, \
             patch('testpilot_cli.logger.error') as mock_logger:
            
            generate("Test specification", "playwright", "javascript", None, "http://localhost:3000")
            
            # Verify error was logged and handled
            mock_logger.assert_called()
            mock_echo.assert_any_call("Error: Service initialization failed", err=True)
            mock_exit.assert_called_with(1)
    
    def test_invalid_format_option(self):
        """Test handling of invalid format option."""
        
        # Mock click.echo and sys.exit
        with patch('testpilot_cli.click.echo') as mock_echo, \
             patch('testpilot_cli.sys.exit') as mock_exit, \
             patch('testpilot_cli.logger.error') as mock_logger:
            
            # This should raise a click.BadParameter
            with pytest.raises(Exception):
                generate("Test specification", "invalid_format", "javascript", None, "http://localhost:3000")


class TestCLIOutputFormatting:
    """Test CLI output formatting."""
    
    @patch('testpilot_cli.AgentService')
    def test_output_to_file(self, mock_agent_service_class, tmp_path):
        """Test output formatting when saving to file."""
        
        # Mock AgentService instance
        mock_agent_service = Mock()
        mock_agent_service_class.return_value = mock_agent_service
        
        # Mock successful response
        mock_agent_service.generate_test_cases.return_value = {
            "success": True,
            "test_cases": "Generated test cases",
            "framework": "playwright",
            "language": "javascript",
            "model_used": "openai"
        }
        
        # Create temporary output file
        output_file = tmp_path / "test_output.json"
        
        # Mock click.echo and sys.exit
        with patch('testpilot_cli.click.echo') as mock_echo, \
             patch('testpilot_cli.sys.exit') as mock_exit:
            
            generate("Test specification", "playwright", "javascript", str(output_file), "http://localhost:3000")
            
            # Verify file was created with correct content
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                output_data = json.load(f)
            
            assert output_data["success"] is True
            assert output_data["test_cases"] == "Generated test cases"
            assert output_data["framework"] == "playwright"
            assert output_data["language"] == "javascript"
            assert output_data["model_used"] == "openai"
            
            # Verify success message was printed
            mock_echo.assert_any_call(f"Results written to: {output_file}")
            mock_exit.assert_called_with(0)


if __name__ == '__main__':
    pytest.main([__file__]) 