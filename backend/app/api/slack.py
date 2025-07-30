"""
Slack API router for handling Slack events and interactions.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import Response
from app.services.slack_service import slack_service
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/slack", tags=["slack"])


@router.get("/events")
async def slack_events_get():
    """Handle GET requests to the events endpoint (for basic connectivity testing)."""
    return {"message": "Slack events endpoint is active", "status": "ok"}


@router.post("/events")
async def slack_events(request: Request):
    """
    Handle Slack events and interactions.
    
    This endpoint receives:
    - Slash commands
    - Interactive messages (button clicks)
    - Event subscriptions
    - URL verification challenges
    """
    try:
        # Get the request body
        body = await request.body()
        body_text = body.decode('utf-8')
        
        # Handle URL verification challenge (both form-encoded and JSON formats)
        if body_text.startswith('challenge='):
            challenge = body_text.split('=')[1]
            logger.info(f"Received Slack URL verification challenge (form): {challenge}")
            return Response(content=challenge, media_type="text/plain")
        
        # Handle JSON format challenge
        try:
            import json
            body_json = json.loads(body_text)
            if body_json.get("type") == "url_verification":
                challenge = body_json.get("challenge", "")
                logger.info(f"Received Slack URL verification challenge (JSON): {challenge}")
                return Response(content=challenge, media_type="text/plain")
        except (json.JSONDecodeError, KeyError):
            pass  # Not a JSON challenge, continue with normal processing
        
        # If Slack service is not available, handle gracefully for URL verification
        if not slack_service.is_available():
            logger.warning("Slack integration not available - returning 200 for URL verification")
            # Return 200 OK for URL verification, even if Slack isn't fully configured
            return Response(content="OK", media_type="text/plain")
        
        # Get the Slack request handler
        handler = slack_service.get_handler()
        if not handler:
            logger.warning("Slack handler not available - returning 200 for URL verification")
            return Response(content="OK", media_type="text/plain")
        
        # Let the Slack Bolt handler process the request
        return await handler.handle(request)
        
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def slack_health():
    """Check Slack integration health."""
    return {
        "slack_available": slack_service.is_available(),
        "credentials_configured": bool(
            settings.slack_signing_secret and 
            settings.slack_bot_token
        ),
        "handler_available": slack_service.get_handler() is not None
    }


@router.post("/send-message")
async def send_message(channel: str, text: str, thread_ts: str = None):
    """Send a message to a Slack channel (for testing)."""
    if not slack_service.is_available():
        raise HTTPException(status_code=503, detail="Slack integration not available")
    
    success = await slack_service.send_message(channel, text, thread_ts)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send message")
    
    return {"status": "sent", "channel": channel}


@router.post("/send-rich-message")
async def send_rich_message(channel: str, blocks: list, thread_ts: str = None):
    """Send a rich message with blocks to a Slack channel (for testing)."""
    if not slack_service.is_available():
        raise HTTPException(status_code=503, detail="Slack integration not available")
    
    success = await slack_service.send_rich_message(channel, blocks, thread_ts)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send rich message")
    
    return {"status": "sent", "channel": channel} 