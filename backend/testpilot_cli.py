#!/usr/bin/env python3
"""
TestPilot CLI - Natural Language Test Generation

Command-line interface for generating test cases from product specifications
using natural language processing.
"""

import click
import json
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.agent_service import AgentService
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_specification(input_path: str) -> str:
    """Load specification from file or return as-is if it's a string."""
    input_path_obj = Path(input_path)
    
    if input_path_obj.exists():
        # It's a file path
        return input_path_obj.read_text()
    else:
        # Assume it's specification text as a string
        return input_path


def save_output(output_data: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """Save output to file or print to stdout."""
    if output_path:
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        click.echo(f"Results written to: {output_path}")
    else:
        # Print to stdout
        click.echo(json.dumps(output_data, indent=2))


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    TestPilot CLI - Generate test cases from natural language specifications.
    
    This tool uses AI to convert product specifications into executable test cases.
    """
    pass


@cli.command()
@click.option(
    '--input', '-i',
    required=True,
    help='Path to specification file or specification text'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['playwright', 'english'], case_sensitive=False),
    default='playwright',
    help='Output format for test cases (default: playwright)'
)
@click.option(
    '--language', '-l',
    type=click.Choice(['javascript', 'python'], case_sensitive=False),
    default='javascript',
    help='Programming language for test cases (default: javascript)'
)
@click.option(
    '--output', '-o',
    help='Output file path (default: stdout)'
)
@click.option(
    '--base-url',
    default='http://localhost:3000',
    help='Base URL for Playwright tests (default: http://localhost:3000)'
)
def generate(input: str, format: str, language: str, output: Optional[str], base_url: str):
    """
    Generate test cases from product specification.
    
    Examples:
    
    \b
    # Generate Playwright tests from a file
    testpilot generate --input spec.md --format playwright
    
    \b
    # Generate English descriptions from text
    testpilot generate --input "User should be able to login" --format english
    
    \b
    # Save output to file
    testpilot generate --input spec.md --output tests.json
    """
    try:
        # Load specification
        specification = load_specification(input)
        
        # Initialize AgentService
        agent_service = AgentService()
        
        # Generate test cases
        if format.lower() == 'playwright':
            result = agent_service.generate_test_cases(
                specification=specification,
                framework='playwright',
                language=language
            )
        elif format.lower() == 'english':
            result = agent_service.generate_english_description(specification)
        else:
            raise click.BadParameter(f"Unsupported format: {format}")
        
        # Handle result
        if result.get('success'):
            save_output(result, output)
            sys.exit(0)
        else:
            click.echo(f"Error generating test cases: {result.get('error')}", err=True)
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test generation failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--test-case', '-t',
    required=True,
    help='Test case description or file path'
)
@click.option(
    '--base-url',
    default='http://localhost:3000',
    help='Base URL for the application (default: http://localhost:3000)'
)
@click.option(
    '--output', '-o',
    help='Output file path (default: stdout)'
)
def playwright(test_case: str, base_url: str, output: Optional[str]):
    """
    Generate Playwright test script from test case description.
    
    Examples:
    
    \b
    # Generate script from description
    testpilot playwright --test-case "User should be able to login"
    
    \b
    # Generate script from file
    testpilot playwright --test-case test_case.txt --base-url https://example.com
    """
    try:
        # Load test case
        test_case_content = load_specification(test_case)
        
        # Initialize AgentService
        agent_service = AgentService()
        
        # Generate Playwright script
        result = agent_service.generate_playwright_script(
            test_case=test_case_content,
            base_url=base_url
        )
        
        # Handle result
        if result.get('success'):
            save_output(result, output)
            sys.exit(0)
        else:
            click.echo(f"Error generating Playwright script: {result.get('error')}", err=True)
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Playwright script generation failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def health():
    """
    Check the health of the TestPilot service.
    
    Verifies that the AgentService is properly configured and can connect to LLM providers.
    """
    try:
        # Initialize AgentService
        agent_service = AgentService()
        
        # Check health
        health_result = agent_service.health_check()
        
        # Check if any LLM is available
        openai_available = health_result.get('openai', {}).get('available', False)
        anthropic_available = health_result.get('anthropic', {}).get('available', False)
        test_query_success = health_result.get('test_query', False)
        
        if (openai_available or anthropic_available) and test_query_success:
            click.echo("✅ TestPilot service is healthy")
            
            # Show available providers
            providers = []
            if openai_available:
                providers.append("OpenAI")
            if anthropic_available:
                providers.append("Anthropic")
            
            click.echo(f"Available providers: {', '.join(providers)}")
            click.echo(f"Test query: ✅ Success")
            sys.exit(0)
        else:
            click.echo("❌ TestPilot service is unhealthy", err=True)
            
            if not (openai_available or anthropic_available):
                click.echo("No LLM providers are available", err=True)
            
            if not test_query_success:
                error_msg = health_result.get('test_error', 'Unknown error')
                click.echo(f"Test query failed: {error_msg}", err=True)
            
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def config():
    """
    Show current TestPilot configuration.
    
    Displays the current configuration including API keys status and settings.
    """
    try:
        config_info = {
            "openai_configured": bool(settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here"),
            "anthropic_configured": bool(settings.anthropic_api_key and settings.anthropic_api_key != "your_anthropic_api_key_here"),
            "debug": settings.debug,
            "host": settings.host,
            "port": settings.port,
            "database_url": "configured" if settings.database_url else "not configured",
            "redis_url": settings.redis_url,
            "gcp_project_id": settings.gcp_project_id or "not configured"
        }
        
        click.echo("TestPilot Configuration:")
        click.echo(json.dumps(config_info, indent=2))
        
    except Exception as e:
        logger.error(f"Config check failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli() 