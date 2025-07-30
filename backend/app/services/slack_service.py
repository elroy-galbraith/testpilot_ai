"""
Slack integration service using Slack Bolt SDK.
Handles slash commands, interactive messages, and event processing.
"""

import logging
from typing import Optional, Dict, Any
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_sdk.errors import SlackApiError
from app.config import settings

logger = logging.getLogger(__name__)


class SlackService:
    """Service for handling Slack integration with TestPilot AI."""
    
    def __init__(self):
        """Initialize the Slack service with Bolt app."""
        self.app = None
        self.handler = None
        self._initialize_app()
    
    def _initialize_app(self):
        """Initialize the Slack Bolt app with proper configuration."""
        try:
            if not settings.slack_signing_secret or not settings.slack_bot_token:
                logger.warning("Slack credentials not configured. Slack integration will be disabled.")
                return
            
            # Initialize the Bolt app
            self.app = App(
                token=settings.slack_bot_token,
                signing_secret=settings.slack_signing_secret
            )
            
            # Create FastAPI request handler
            self.handler = SlackRequestHandler(self.app)
            
            # Register event handlers
            self._register_handlers()
            
            logger.info("Slack Bolt app initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Slack app: {e}")
            self.app = None
            self.handler = None
    
    def _register_handlers(self):
        """Register all Slack event handlers."""
        if not self.app:
            return
        
        # Register slash command handler
        @self.app.command("/testpilot")
        async def handle_testpilot_command(ack, command, say):
            """Handle /testpilot slash command."""
            try:
                # Acknowledge the command immediately
                await ack()
                
                # Extract the user's request
                user_request = command.get("text", "").strip()
                user_id = command.get("user_id")
                channel_id = command.get("channel_id")
                
                if not user_request:
                    await say(
                        text="Please provide a test request. For example: `/testpilot test the login functionality`",
                        thread_ts=command.get("ts")
                    )
                    return
                
                # Send initial response
                response = await say(
                    text=f"🤖 Processing your test request: *{user_request}*\n\nI'll generate and run tests for you. This may take a moment...",
                    thread_ts=command.get("ts")
                )
                
                # TODO: Integrate with TestPilot AI backend
                # For now, send a placeholder response
                await self._process_test_request(user_request, user_id, channel_id, response["ts"])
                
            except Exception as e:
                logger.error(f"Error handling /testpilot command: {e}")
                await say(
                    text="❌ Sorry, I encountered an error processing your request. Please try again.",
                    thread_ts=command.get("ts")
                )
        
        # Register interactive message handler
        @self.app.action("view_logs")
        async def handle_view_logs(ack, body, say):
            """Handle 'View Logs' button click."""
            await ack()
            # TODO: Implement logs viewing functionality
            await say(text="📋 Logs viewer coming soon!")
        
        @self.app.action("view_screenshot")
        async def handle_view_screenshot(ack, body, say):
            """Handle 'View Screenshot' button click."""
            await ack()
            # TODO: Implement screenshot viewing functionality
            await say(text="📸 Screenshot viewer coming soon!")
        
        @self.app.action("rerun_test")
        async def handle_rerun_test(ack, body, say):
            """Handle 'Rerun Test' button click."""
            await ack()
            # TODO: Implement test rerun functionality
            await say(text="🔄 Test rerun functionality coming soon!")
    
    async def _process_test_request(self, user_request: str, user_id: str, channel_id: str, thread_ts: str):
        """Process a test request from Slack."""
        try:
            # Send initial processing message
            await self.app.client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text="🔄 Generating test cases...",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Processing:* {user_request}\n\n🤖 I'm analyzing your request and generating test cases..."
                        }
                    }
                ]
            )
            
            # Call TestPilot AI backend to generate tests
            test_case = await self._generate_test_case(user_request)
            
            if not test_case:
                await self.app.client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=thread_ts,
                    text="❌ Failed to generate test cases",
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Error:* Failed to generate test cases for: {user_request}\n\nPlease try again or provide more specific details."
                            }
                        }
                    ]
                )
                return
            
            # Execute the generated test
            execution_result = await self._execute_test(test_case["id"])
            
            if not execution_result:
                await self.app.client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=thread_ts,
                    text="❌ Failed to execute test",
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Error:* Generated test case but failed to execute it.\n\n*Test Case ID:* {test_case['id']}"
                            }
                        }
                    ]
                )
                return
            
            # Send comprehensive test results
            await self._send_test_results(channel_id, thread_ts, user_request, test_case, execution_result)
            
        except Exception as e:
            logger.error(f"Error processing test request: {e}")
            await self.app.client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text="❌ Error processing request",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Error:* {str(e)}\n\nPlease try again or contact support."
                        }
                    }
                ]
            )
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e}")
        except Exception as e:
            logger.error(f"Error processing test request: {e}")

    async def _generate_test_case(self, user_request: str) -> Optional[Dict]:
        """Generate a test case using the TestPilot AI backend."""
        try:
            import httpx
            import json
            
            # Prepare the request payload
            payload = {
                "spec": user_request,
                "framework": "playwright",
                "language": "javascript",
                "title": f"Slack Test: {user_request[:50]}...",
                "description": f"Test generated from Slack request: {user_request}"
            }
            
            # Call the test generation API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/api/v1/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Generated test case: {result}")
                    return result
                else:
                    logger.error(f"Failed to generate test case: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error generating test case: {e}")
            return None

    async def _execute_test(self, test_case_id: int) -> Optional[Dict]:
        """Execute a test case using the TestPilot AI backend."""
        try:
            import httpx
            
            # Prepare the execution request
            payload = {
                "test_case_id": test_case_id,
                "browser": "chromium",
                "headless": True,
                "timeout": 30000,
                "retry_count": 3,
                "retry_delay": 1000,
                "screenshot_on_failure": True,
                "capture_logs": True
            }
            
            # Call the test execution API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/api/v1/execute",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Executed test: {result}")
                    return result
                else:
                    logger.error(f"Failed to execute test: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error executing test: {e}")
            return None

    async def _send_test_results(self, channel_id: str, thread_ts: str, user_request: str, test_case: Dict, execution_result: Dict):
        """Send comprehensive test results to Slack."""
        try:
            # Get detailed execution results
            execution_id = execution_result.get("execution_id")
            if execution_id:
                detailed_results = await self._get_execution_results(execution_id)
            else:
                detailed_results = None
            
            # Prepare the result message
            status_emoji = "✅" if execution_result.get("status") == "completed" else "❌"
            status_text = execution_result.get("status", "unknown").title()
            
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Test Results for:* {user_request}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Status:* {status_emoji} {status_text}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Test Case ID:* {test_case.get('test_case_id', 'N/A')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Execution ID:* {execution_id or 'N/A'}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Framework:* {test_case.get('framework', 'N/A')}"
                        }
                    ]
                }
            ]
            
            # Add detailed results if available
            if detailed_results:
                execution_time = detailed_results.get("execution_time", 0)
                error_message = detailed_results.get("error_message")
                
                if error_message:
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Error:* {error_message}"
                        }
                    })
                else:
                    blocks.append({
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Duration:* {execution_time:.2f}s"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Browser:* {detailed_results.get('browser_info', {}).get('name', 'N/A')}"
                            }
                        ]
                    })
            
            # Add action buttons
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Logs"
                        },
                        "action_id": "view_logs",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Screenshot"
                        },
                        "action_id": "view_screenshot"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Rerun Test"
                        },
                        "action_id": "rerun_test",
                        "style": "secondary"
                    }
                ]
            })
            
            await self.app.client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=f"{status_emoji} Test execution completed!",
                blocks=blocks
            )
            
        except Exception as e:
            logger.error(f"Error sending test results: {e}")
            await self.app.client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text="✅ Test execution completed!",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Test Results for:* {user_request}\n\n*Status:* ✅ Completed\n*Test Case ID:* {test_case.get('test_case_id', 'N/A')}\n*Execution ID:* {execution_result.get('execution_id', 'N/A')}"
                        }
                    }
                ]
            )

    async def _get_execution_results(self, execution_id: int) -> Optional[Dict]:
        """Get detailed execution results from the TestPilot AI backend."""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://localhost:8000/api/v1/results/{execution_id}",
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get execution results: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting execution results: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if Slack integration is available."""
        return self.app is not None and self.handler is not None
    
    def get_handler(self) -> Optional[SlackRequestHandler]:
        """Get the FastAPI request handler."""
        return self.handler
    
    async def send_message(self, channel: str, text: str, thread_ts: Optional[str] = None) -> bool:
        """Send a message to a Slack channel."""
        if not self.app:
            return False
        
        try:
            await self.app.client.chat_postMessage(
                channel=channel,
                text=text,
                thread_ts=thread_ts
            )
            return True
        except SlackApiError as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False
    
    async def send_rich_message(self, channel: str, blocks: list, thread_ts: Optional[str] = None) -> bool:
        """Send a rich message with blocks to a Slack channel."""
        if not self.app:
            return False
        
        try:
            await self.app.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                thread_ts=thread_ts
            )
            return True
        except SlackApiError as e:
            logger.error(f"Failed to send rich Slack message: {e}")
            return False


# Global Slack service instance
slack_service = SlackService() 