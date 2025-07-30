# Slack Integration Setup Guide

This guide explains how to set up the Slack integration for TestPilot AI.

## Prerequisites

1. A Slack workspace where you have admin permissions
2. The TestPilot AI backend running
3. A publicly accessible URL for your backend (for Slack webhooks)

## Step 1: Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Enter app name: "TestPilot AI"
5. Select your workspace
6. Click "Create App"

## Step 2: Configure App Settings

### Basic Information
1. In your app settings, note down:
   - **Signing Secret** (under "Basic Information" → "App Credentials")
   - **Bot User OAuth Token** (under "OAuth & Permissions")

### OAuth & Permissions
1. Go to "OAuth & Permissions"
2. Add the following Bot Token Scopes:
   - `commands` - For slash commands
   - `chat:write` - To send messages
   - `chat:write.public` - To send messages in public channels
   - `channels:read` - To read channel information
   - `users:read` - To read user information

3. Click "Install to Workspace"
4. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

### Slash Commands
1. Go to "Slash Commands"
2. Click "Create New Command"
3. Configure:
   - **Command**: `/testpilot`
   - **Request URL**: `https://your-domain.com/slack/events`
   - **Short Description**: "Generate and run tests with AI"
   - **Usage Hint**: "test the login functionality"
4. Click "Save"

### Event Subscriptions
1. Go to "Event Subscriptions"
2. Enable Events
3. Set **Request URL**: `https://your-domain.com/slack/events`
4. **Important**: The endpoint will automatically handle Slack's URL verification challenge (both JSON and form-encoded formats)
5. Subscribe to bot events:
   - `message.im` - Direct messages to the bot
   - `app_mention` - When the bot is mentioned

## Step 3: Configure Environment Variables

Add the following variables to your `.env` file:

```bash
# Slack Configuration
SLACK_SIGNING_SECRET=your_slack_signing_secret_here
SLACK_BOT_TOKEN=xoxb-your_slack_bot_token_here
SLACK_APP_TOKEN=xapp-your_slack_app_token_here
```

## Step 4: Install Dependencies

Install the Slack Bolt SDK:

```bash
pip install -r requirements.txt
```

## Step 5: Test the Integration

1. Start your backend server:
   ```bash
   python main.py
   ```

2. Check the health endpoint:
   ```bash
   curl http://localhost:8000/slack/health
   ```

3. In your Slack workspace, try the slash command:
   ```
   /testpilot test the login functionality
   ```

## Step 6: Development with ngrok (Optional)

For local development, use ngrok to expose your local server:

1. Install ngrok: https://ngrok.com/
2. Start your backend server:
   ```bash
   cd backend
   python main.py
   ```
   The server will start on port 8000 by default.

3. In a new terminal, run ngrok with the correct port:
   ```bash
   ngrok http 8000
   ```
   **Important**: Use port 8000, not 8080 or 80!

4. Copy the ngrok URL (e.g., `https://abc123.ngrok-free.app`) and add `/slack/events` to it
5. Test the endpoint before configuring Slack:
   ```bash
   curl https://abc123.ngrok-free.app/slack/events
   ```
   You should see: `{"message": "Slack events endpoint is active", "status": "ok"}`

6. Use this full URL as your Request URL in Slack app settings:
   ```
   https://abc123.ngrok-free.app/slack/events
   ```

## Troubleshooting

### Common Issues

1. **"Your URL didn't respond with the value of the challenge parameter"**
   - This is now automatically handled by the updated endpoint
   - Make sure your backend is running and accessible
   - Check that the Request URL is exactly: `https://your-domain.com/slack/events`
   - Try clicking "Retry" in the Slack app settings

2. **ngrok ERR_NGROK_8012: "connection refused"**
   - **Most common cause**: Wrong port in ngrok command
   - **Solution**: Use `ngrok http 8000` (not 8080 or 80)
   - **Verify**: Your FastAPI server is running on port 8000
   - **Check**: Run `curl http://localhost:8000/health` to verify server is up

2. **"Slack integration not configured"**
   - Check that all environment variables are set correctly
   - Verify the signing secret and bot token are valid

3. **"Invalid request signature"**
   - Ensure the signing secret matches exactly
   - Check that the request URL is correct

4. **"Command not found"**
   - Verify the slash command is installed in your workspace
   - Check that the Request URL is accessible

5. **"Permission denied"**
   - Ensure the bot has the required OAuth scopes
   - Check that the bot is installed in the workspace

### Debug Mode

Enable debug logging by setting `DEBUG=true` in your `.env` file.

## Security Considerations

1. **Never commit your Slack tokens to version control**
2. **Use environment variables for all sensitive data**
3. **Verify request signatures in production**
4. **Use HTTPS in production environments**
5. **Regularly rotate your Slack tokens**

## API Endpoints

- `POST /slack/events` - Handle Slack events and interactions
- `GET /slack/health` - Check Slack integration health
- `POST /slack/send-message` - Send a message to a channel (testing)
- `POST /slack/send-rich-message` - Send a rich message with blocks (testing)

## Integration with TestPilot AI

The Slack integration connects to the following TestPilot AI services:

- **Test Generation**: Converts natural language requests into test cases
- **Test Execution**: Runs the generated tests
- **Result Reporting**: Sends test results back to Slack with rich formatting
- **Interactive Actions**: Allows users to view logs, screenshots, and rerun tests

## Next Steps

1. Integrate with the TestPilot AI backend services
2. Add more interactive features (buttons, modals)
3. Implement user authentication and authorization
4. Add support for multiple workspaces
5. Create admin commands for workspace management 