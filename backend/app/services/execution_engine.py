"""
Playwright-based Test Execution Engine

This module provides a Python interface for executing Playwright test scripts
headlessly and collecting artifacts like screenshots and logs.
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union
import uuid

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

logger = logging.getLogger(__name__)


@dataclass
class ExecutionConfig:
    """Configuration for test execution."""
    browser: str = "chromium"  # chromium, firefox, webkit
    headless: bool = True
    timeout: int = 30000  # milliseconds
    retry_count: int = 3
    retry_delay: int = 1000  # milliseconds
    screenshot_on_failure: bool = True
    capture_logs: bool = True
    viewport_width: int = 1280
    viewport_height: int = 720
    user_agent: Optional[str] = None
    extra_args: List[str] = field(default_factory=list)


@dataclass
class ExecutionResult:
    """Result of test execution."""
    success: bool
    test_id: str
    execution_time: float
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    logs: List[Dict] = field(default_factory=list)
    console_logs: List[Dict] = field(default_factory=list)
    network_logs: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class PlaywrightExecutionEngine:
    """
    Playwright-based test execution engine.
    
    This class provides methods to execute Playwright test scripts,
    handle retries, capture artifacts, and manage browser instances.
    """
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        """Initialize the execution engine with configuration."""
        self.config = config or ExecutionConfig()
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._temp_dir: Optional[Path] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
    
    async def start(self):
        """Start the Playwright browser instance."""
        try:
            logger.info("Starting Playwright execution engine")
            self.playwright = await async_playwright().start()
            
            # Launch browser based on configuration
            if self.config.browser == "chromium":
                self.browser = await self.playwright.chromium.launch(
                    headless=self.config.headless,
                    args=self.config.extra_args
                )
            elif self.config.browser == "firefox":
                self.browser = await self.playwright.firefox.launch(
                    headless=self.config.headless
                )
            elif self.config.browser == "webkit":
                self.browser = await self.playwright.webkit.launch(
                    headless=self.config.headless
                )
            else:
                raise ValueError(f"Unsupported browser: {self.config.browser}")
            
            # Create browser context
            context_options = {
                "viewport": {
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height
                }
            }
            
            if self.config.user_agent:
                context_options["user_agent"] = self.config.user_agent
            
            self.context = await self.browser.new_context(**context_options)
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set default timeout
            self.page.set_default_timeout(self.config.timeout)
            
            # Create temporary directory for artifacts
            self._temp_dir = Path(tempfile.mkdtemp(prefix="playwright_exec_"))
            logger.info(f"Playwright execution engine started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Playwright execution engine: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the Playwright browser instance and cleanup."""
        try:
            if self.page:
                await self.page.close()
                self.page = None
                
            if self.context:
                await self.context.close()
                self.context = None
                
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            logger.info("Playwright execution engine stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Playwright execution engine: {e}")
    
    async def execute_test(self, test_code: str, test_id: Optional[str] = None) -> ExecutionResult:
        """
        Execute a Playwright test script with retry logic.
        
        Args:
            test_code: The Playwright test script to execute
            test_id: Optional test identifier for tracking
            
        Returns:
            ExecutionResult with execution details and artifacts
        """
        if not test_id:
            test_id = str(uuid.uuid4())
            
        logger.info(f"Starting test execution for test_id: {test_id}")
        start_time = time.time()
        
        # Initialize result
        result = ExecutionResult(
            success=False,
            test_id=test_id,
            execution_time=0.0
        )
        
        # Ensure engine is started
        if not self.playwright:
            await self.start()
        
        # Execute with retry logic
        for attempt in range(self.config.retry_count):
            try:
                logger.info(f"Test execution attempt {attempt + 1}/{self.config.retry_count}")
                
                # Reset page state for retry
                if attempt > 0:
                    await self._reset_page_state()
                
                # Execute the test
                await self._execute_test_code(test_code, result)
                
                # If we get here, test passed
                result.success = True
                break
                
            except Exception as e:
                logger.warning(f"Test execution attempt {attempt + 1} failed: {e}")
                result.error_message = str(e)
                
                # Capture artifacts on failure
                if self.config.screenshot_on_failure:
                    await self._capture_screenshot(result)
                
                if self.config.capture_logs:
                    await self._capture_logs(result)
                
                # Wait before retry (except on last attempt)
                if attempt < self.config.retry_count - 1:
                    await asyncio.sleep(self.config.retry_delay / 1000)
        
        result.execution_time = time.time() - start_time
        
        if result.success:
            logger.info(f"Test execution completed successfully in {result.execution_time:.2f}s")
        else:
            logger.error(f"Test execution failed after {self.config.retry_count} attempts")
        
        return result
    
    async def _execute_test_code(self, test_code: str, result: ExecutionResult):
        """Execute the actual test code."""
        # Create a temporary test file
        test_file = self._temp_dir / f"test_{result.test_id}.js"
        
        try:
            # Write test code to file
            test_file.write_text(test_code)
            
            # Execute the test using Playwright's test runner
            await self._run_playwright_test(test_file, result)
            
        finally:
            # Clean up temporary file
            if test_file.exists():
                test_file.unlink()
    
    async def _run_playwright_test(self, test_file: Path, result: ExecutionResult):
        """Run the Playwright test using the test runner."""
        # This is a simplified implementation
        # In a full implementation, you would use Playwright's test runner
        # For now, we'll execute the code directly in the browser context
        
        # Navigate to a blank page
        await self.page.goto("about:blank")
        
        # Execute the test code in the browser context with proper error handling
        try:
            await self.page.evaluate(f"""
                (async () => {{
                    try {{
                        {test_file.read_text()}
                    }} catch (error) {{
                        // Re-throw the error so it's caught by the Python code
                        throw error;
                    }}
                }})();
            """)
        except Exception as e:
            # Re-throw the exception to be caught by the retry logic
            raise e
    
    async def _reset_page_state(self):
        """Reset the page state for retry attempts."""
        if self.page:
            # Navigate to blank page
            await self.page.goto("about:blank")
            
            # Clear cookies and storage
            await self.context.clear_cookies()
            
            # Clear console logs
            await self.page.evaluate("console.clear()")
    
    async def _capture_screenshot(self, result: ExecutionResult):
        """Capture a screenshot on test failure."""
        try:
            if self.page:
                screenshot_path = self._temp_dir / f"screenshot_{result.test_id}.png"
                await self.page.screenshot(path=str(screenshot_path), full_page=True)
                result.screenshot_path = str(screenshot_path)
                logger.info(f"Screenshot captured: {screenshot_path}")
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
    
    async def _capture_logs(self, result: ExecutionResult):
        """Capture console and network logs."""
        try:
            if self.page:
                # Capture console logs
                console_logs = await self.page.evaluate("""
                    () => {
                        return window.console.logs || [];
                    }
                """)
                result.console_logs = console_logs
                
                # Capture network logs (if available)
                # This would require setting up network event listeners
                result.network_logs = []
                
                logger.info(f"Captured {len(console_logs)} console log entries")
        except Exception as e:
            logger.error(f"Failed to capture logs: {e}")


class ExecutionEngineManager:
    """
    Manager class for handling multiple execution engines and providing
    a simplified interface for test execution.
    """
    
    def __init__(self):
        self.engines: Dict[str, PlaywrightExecutionEngine] = {}
    
    async def execute_test(
        self,
        test_code: str,
        config: Optional[ExecutionConfig] = None,
        test_id: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute a test using a managed execution engine.
        
        Args:
            test_code: The Playwright test script to execute
            config: Execution configuration
            test_id: Optional test identifier
            
        Returns:
            ExecutionResult with execution details
        """
        if not test_id:
            test_id = str(uuid.uuid4())
        
        # Create or reuse engine
        engine = self.engines.get(test_id)
        if not engine:
            engine = PlaywrightExecutionEngine(config)
            self.engines[test_id] = engine
        
        try:
            # Execute the test
            result = await engine.execute_test(test_code, test_id)
            return result
        finally:
            # Clean up engine
            if test_id in self.engines:
                await self.engines[test_id].stop()
                del self.engines[test_id]
    
    async def cleanup(self):
        """Clean up all managed engines."""
        for engine in self.engines.values():
            await engine.stop()
        self.engines.clear()


# Global execution engine manager instance
execution_manager = ExecutionEngineManager() 