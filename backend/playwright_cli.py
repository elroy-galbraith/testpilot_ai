#!/usr/bin/env python3
"""
Playwright Test Execution CLI

Command-line interface for executing Playwright test scripts.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from app.services.execution_engine import (
    ExecutionConfig,
    PlaywrightExecutionEngine,
    execution_manager
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Execute Playwright test scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Execute a test file
  python playwright_cli.py execute --input test.js --browser chromium
  
  # Execute with custom configuration
  python playwright_cli.py execute --input test.js --browser firefox --timeout 60000 --retry-count 5
  
  # Execute with headful mode for debugging
  python playwright_cli.py execute --input test.js --headless false
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Execute command
    execute_parser = subparsers.add_parser('execute', help='Execute a test script')
    execute_parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to the test script file or test code string'
    )
    execute_parser.add_argument(
        '--browser', '-b',
        choices=['chromium', 'firefox', 'webkit'],
        default='chromium',
        help='Browser to use for execution (default: chromium)'
    )
    execute_parser.add_argument(
        '--headless',
        type=lambda x: x.lower() == 'true',
        default=True,
        help='Run in headless mode (default: true)'
    )
    execute_parser.add_argument(
        '--timeout', '-t',
        type=int,
        default=30000,
        help='Test timeout in milliseconds (default: 30000)'
    )
    execute_parser.add_argument(
        '--retry-count', '-r',
        type=int,
        default=3,
        help='Number of retry attempts (default: 3)'
    )
    execute_parser.add_argument(
        '--retry-delay',
        type=int,
        default=1000,
        help='Delay between retries in milliseconds (default: 1000)'
    )
    execute_parser.add_argument(
        '--viewport-width',
        type=int,
        default=1280,
        help='Viewport width (default: 1280)'
    )
    execute_parser.add_argument(
        '--viewport-height',
        type=int,
        default=720,
        help='Viewport height (default: 720)'
    )
    execute_parser.add_argument(
        '--user-agent',
        help='Custom user agent string'
    )
    execute_parser.add_argument(
        '--output', '-o',
        help='Output file for results (JSON format)'
    )
    execute_parser.add_argument(
        '--test-id',
        help='Custom test identifier'
    )
    execute_parser.add_argument(
        '--no-screenshot',
        action='store_true',
        help='Disable screenshot capture on failure'
    )
    execute_parser.add_argument(
        '--no-logs',
        action='store_true',
        help='Disable log capture'
    )
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install Playwright browsers')
    install_parser.add_argument(
        '--browsers',
        nargs='+',
        choices=['chromium', 'firefox', 'webkit'],
        default=['chromium'],
        help='Browsers to install (default: chromium)'
    )
    
    return parser.parse_args()


async def install_browsers(browsers: list):
    """Install Playwright browsers."""
    try:
        import subprocess
        
        logger.info(f"Installing Playwright browsers: {', '.join(browsers)}")
        
        # Install Playwright browsers
        cmd = ['playwright', 'install'] + browsers
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Playwright browsers installed successfully")
        else:
            logger.error(f"Failed to install browsers: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error installing browsers: {e}")
        return False
    
    return True


def load_test_code(input_path: str) -> str:
    """Load test code from file or return as-is if it's a string."""
    input_path_obj = Path(input_path)
    
    if input_path_obj.exists():
        # It's a file path
        return input_path_obj.read_text()
    else:
        # Assume it's test code as a string
        return input_path


async def execute_test(args):
    """Execute a test script."""
    try:
        # Load test code
        test_code = load_test_code(args.input)
        
        # Create execution configuration
        config = ExecutionConfig(
            browser=args.browser,
            headless=args.headless,
            timeout=args.timeout,
            retry_count=args.retry_count,
            retry_delay=args.retry_delay,
            viewport_width=args.viewport_width,
            viewport_height=args.viewport_height,
            user_agent=args.user_agent,
            screenshot_on_failure=not args.no_screenshot,
            capture_logs=not args.no_logs
        )
        
        logger.info(f"Executing test with browser: {args.browser}")
        logger.info(f"Configuration: {config}")
        
        # Execute the test
        result = await execution_manager.execute_test(
            test_code=test_code,
            config=config,
            test_id=args.test_id
        )
        
        # Prepare output
        output_data = {
            'success': result.success,
            'test_id': result.test_id,
            'execution_time': result.execution_time,
            'error_message': result.error_message,
            'screenshot_path': result.screenshot_path,
            'console_logs': result.console_logs,
            'network_logs': result.network_logs,
            'metadata': result.metadata
        }
        
        # Output results
        if args.output:
            # Write to file
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            logger.info(f"Results written to: {args.output}")
        else:
            # Print to stdout
            print(json.dumps(output_data, indent=2))
        
        # Exit with appropriate code
        sys.exit(0 if result.success else 1)
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


async def main():
    """Main CLI entry point."""
    args = parse_args()
    
    if not args.command:
        print("Error: No command specified")
        print("Use --help for usage information")
        sys.exit(1)
    
    try:
        if args.command == 'install':
            success = await install_browsers(args.browsers)
            sys.exit(0 if success else 1)
        elif args.command == 'execute':
            await execute_test(args)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        # Clean up execution manager
        await execution_manager.cleanup()


if __name__ == '__main__':
    asyncio.run(main()) 