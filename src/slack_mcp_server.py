# src/slack_mcp_server.py
# Slack MCP Server - A comprehensive MCP server for Slack API operations
# Copyright (c) 2025 Brennon Church
# Licensed under the MIT License

import os
import logging
from mcp.server.fastmcp import FastMCP

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("slack", description="A comprehensive MCP server for Slack API operations")

# Import all tool modules to register tools
import sys
from pathlib import Path

# Add src directory to path if not already there
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import tool modules
from slack_mcp.tools import (
    core,
    message_management,
    channel_management,
    user_management,
    files
)

# Register all tools
core.register_tools(mcp)
message_management.register_tools(mcp)
channel_management.register_tools(mcp)
user_management.register_tools(mcp)
files.register_tools(mcp)

def run_server():
    """Run the MCP server for Slack integration."""
    logger.info("Starting Slack MCP server...")
    
    # Try to initialize Slack client from environment
    from slack_mcp.utils.client import init_client_from_env
    
    if init_client_from_env():
        logger.info("Slack client initialized from environment variable")
    else:
        logger.info("No SLACK_BOT_TOKEN found in environment. Use set_slack_token tool to configure.")
    
    mcp.run(transport='stdio')

if __name__ == "__main__":
    run_server()
