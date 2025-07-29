#!/usr/bin/env python3
"""
Test script for the Playwright execution engine.
"""

import asyncio
import json
import logging
import tempfile
from pathlib import Path

from app.services.execution_engine import ExecutionConfig, PlaywrightExecutionEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_successful_execution():
    """Test successful test execution."""
    logger.info("Testing successful execution...")
    
    # Read test code from the sample test file
    test_code = Path("sample_test.js").read_text()
    
    config = ExecutionConfig(
        browser="chromium",
        headless=True,
        timeout=30000,
        retry_count=1
    )
    
    async with PlaywrightExecutionEngine(config) as engine:
        result = await engine.execute_test(test_code, "test_success")
        
        print(f"Success test result: {result.success}")
        print(f"Execution time: {result.execution_time:.2f}s")
        print(f"Error message: {result.error_message}")
        
        assert result.success, "Test should have passed"
        assert not result.error_message, "Should not have error message"
        
        logger.info("✅ Successful execution test passed")


async def test_failing_execution():
    """Test failing test execution with retry logic."""
    logger.info("Testing failing execution with retries...")
    
    # Read test code from the failing test file
    test_code = Path("failing_test.js").read_text()
    
    config = ExecutionConfig(
        browser="chromium",
        headless=True,
        timeout=10000,
        retry_count=2,
        retry_delay=500,
        screenshot_on_failure=True,
        capture_logs=True
    )
    
    async with PlaywrightExecutionEngine(config) as engine:
        result = await engine.execute_test(test_code, "test_failure")
        
        print(f"Failure test result: {result.success}")
        print(f"Execution time: {result.execution_time:.2f}s")
        print(f"Error message: {result.error_message}")
        print(f"Screenshot path: {result.screenshot_path}")
        print(f"Console logs count: {len(result.console_logs)}")
        
        assert not result.success, "Test should have failed"
        assert result.error_message, "Should have error message"
        assert result.screenshot_path, "Should have screenshot on failure"
        
        logger.info("✅ Failing execution test passed")


async def test_different_browsers():
    """Test execution with different browsers."""
    browsers = ["chromium", "firefox", "webkit"]
    
    for browser in browsers:
        logger.info(f"Testing with browser: {browser}")
        
        test_code = """
        async function test() {
            await page.goto('https://example.com');
            await page.waitForLoadState('networkidle');
            const title = await page.title();
            console.log('Page title:', title);
        }
        test();
        """
        
        config = ExecutionConfig(
            browser=browser,
            headless=True,
            timeout=30000,
            retry_count=1
        )
        
        try:
            async with PlaywrightExecutionEngine(config) as engine:
                result = await engine.execute_test(test_code, f"test_{browser}")
                
                print(f"{browser} test result: {result.success}")
                print(f"Execution time: {result.execution_time:.2f}s")
                
                assert result.success, f"{browser} test should have passed"
                logger.info(f"✅ {browser} test passed")
                
        except Exception as e:
            logger.warning(f"⚠️ {browser} test failed: {e}")


async def test_file_execution():
    """Test execution from file."""
    logger.info("Testing execution from file...")
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write("""
        async function test() {
            await page.goto('https://example.com');
            await page.waitForLoadState('networkidle');
            const title = await page.title();
            if (!title.includes('Example Domain')) {
                throw new Error('Title validation failed');
            }
            console.log('File test passed');
        }
        test();
        """)
        test_file_path = f.name
    
    try:
        # Read the file content
        test_code = Path(test_file_path).read_text()
        
        config = ExecutionConfig(
            browser="chromium",
            headless=True,
            timeout=30000,
            retry_count=1
        )
        
        async with PlaywrightExecutionEngine(config) as engine:
            result = await engine.execute_test(test_code, "test_file")
            
            print(f"File test result: {result.success}")
            print(f"Execution time: {result.execution_time:.2f}s")
            
            assert result.success, "File test should have passed"
            logger.info("✅ File execution test passed")
            
    finally:
        # Clean up temporary file
        Path(test_file_path).unlink()


async def main():
    """Run all tests."""
    logger.info("Starting Playwright execution engine tests...")
    
    try:
        # Test successful execution
        await test_successful_execution()
        
        # Test failing execution with retries
        await test_failing_execution()
        
        # Test different browsers
        await test_different_browsers()
        
        # Test file execution
        await test_file_execution()
        
        logger.info("🎉 All tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(main()) 