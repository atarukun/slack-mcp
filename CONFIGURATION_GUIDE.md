# Slack MCP Server Configuration Guide

This guide provides the correct configuration examples for different MCP clients.

## 🚀 For Warp.dev (CORRECTED)

**Use this configuration format for Warp:**

```json
{
  "slack-mcp": {
    "command": "docker",
    "args": [
      "run",
      "--rm",
      "-i",
      "-e",
      "SLACK_BOT_TOKEN=xoxb-your-actual-slack-bot-token",
      "slack-mcp:latest"
    ],
    "env": {},
    "working_directory": null,
    "start_on_launch": true
  }
}
```

### Key Differences for Warp:
- ✅ **No `mcpServers` wrapper** - Warp uses a flat structure
- ✅ **Token in args** - Environment variable passed as `-e` flag in Docker args
- ✅ **Empty env object** - Environment variables go in the args, not env section
- ✅ **Warp-specific fields** - `working_directory` and `start_on_launch`

## 🖥️ For Claude Desktop

**Use this configuration format for Claude Desktop:**

```json
{
  "mcpServers": {
    "slack": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "SLACK_BOT_TOKEN=xoxb-your-actual-slack-bot-token",
        "slack-mcp:latest"
      ],
      "env": {}
    }
  }
}
```

### Key Differences for Claude Desktop:
- ✅ **Requires `mcpServers` wrapper** - Claude Desktop expects this structure
- ✅ **Token in args** - Same pattern as Warp
- ✅ **No Warp-specific fields** - Only command, args, env

## 🐍 Alternative: Direct Python Execution

**For Warp (using virtual environment):**
```json
{
  "slack-mcp": {
    "command": "/home/ataru/repos/slack-mcp/.venv/bin/python",
    "args": ["/home/ataru/repos/slack-mcp/main.py"],
    "env": {
      "SLACK_BOT_TOKEN": "xoxb-your-actual-slack-bot-token"
    },
    "working_directory": "/home/ataru/repos/slack-mcp",
    "start_on_launch": true
  }
}
```

**For Claude Desktop (using virtual environment):**
```json
{
  "mcpServers": {
    "slack": {
      "command": "/home/ataru/repos/slack-mcp/.venv/bin/python",
      "args": ["/home/ataru/repos/slack-mcp/main.py"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-actual-slack-bot-token"
      }
    }
  }
}
```

## 📋 Setup Checklist

1. **Build the Docker image:**
   ```bash
   docker build -t slack-mcp:latest .
   ```

2. **Get your Slack bot token:**
   - Go to https://api.slack.com/apps
   - Create or select your app
   - Go to "OAuth & Permissions"
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)

3. **Replace the token:**
   - Replace `xoxb-your-actual-slack-bot-token` with your real token

4. **Configure in your MCP client:**
   - **Warp**: Use the flat structure without `mcpServers`
   - **Claude Desktop**: Use the nested structure with `mcpServers`

## ⚠️ Important Notes

- **Token Security**: Never commit real tokens to version control
- **Docker Image**: Ensure `slack-mcp:latest` is built before configuring
- **Permissions**: Bot needs appropriate Slack permissions for the tools you want to use
- **Format Differences**: Warp and Claude Desktop use different configuration structures

## 🧪 Testing

After configuration, test with:
- `test_slack_connection` - Verify authentication and workspace access
- `list_channels` - See available channels
- `send_message` - Send a test message

The configuration format differences were the key issue - thank you for providing the working example!
