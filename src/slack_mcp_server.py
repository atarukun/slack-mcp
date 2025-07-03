# src/slack_mcp_server.py

import os
import asyncio
from typing import Any
from mcp.server.fastmcp import FastMCP
from slack_sdk import WebClient
import httpx

# Initialize FastMCP server
mcp = FastMCP("slack")

# Set up the Slack WebClient with environment variables
slack_client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))

async def run_server():
    """Run the MCP server for Slack integration."""
    mcp.run(transport='stdio')

if __name__ == "__main__":
    asyncio.run(run_server())
