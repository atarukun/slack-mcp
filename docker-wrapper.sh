#!/bin/bash
# Docker wrapper script for Slack MCP server
# This script runs the containerized MCP server with STDIO transport
# Designed for use with MCP clients like Claude Desktop or Warp

# Ensure the Docker image exists
if ! docker image inspect slack-mcp:latest >/dev/null 2>&1; then
    echo "Error: Docker image 'slack-mcp:latest' not found." >&2
    echo "Please run: docker build -t slack-mcp:latest ." >&2
    exit 1
fi

# Run the container with proper STDIO handling for MCP
docker run --rm -i \
  -e SLACK_BOT_TOKEN="$SLACK_BOT_TOKEN" \
  slack-mcp:latest
