# src/slack_mcp_server.py
# Slack MCP Server - A comprehensive MCP server for Slack API operations
# Copyright (c) 2025 Brennon Church
# Licensed under the MIT License

import os
import logging
import asyncio
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from slack_sdk import WebClient
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
import httpx
import time
import json
from datetime import datetime

# Import utilities and models from the new package structure
try:
    # Try absolute import first (when installed as package)
    from slack_mcp.utils import (
        # Client utilities
        MCP_USER_AGENT,
        validate_slack_token,
        init_async_client,
        get_slack_client,
        set_slack_client,
        get_async_slack_client,
        # Formatting utilities
        format_file_info,
        # Error handling utilities
        MIN_API_INTERVAL,
        rate_limit_check,
        make_slack_request,
    )
    from slack_mcp.models import (
        SlackTokenValidation,
        ChannelInfo,
        MessageInfo,
        UserInfo,
        FileUploadInfo,
    )
except ImportError:
    # Fall back to relative import (when running directly)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from slack_mcp.utils import (
        # Client utilities
        MCP_USER_AGENT,
        validate_slack_token,
        init_async_client,
        get_slack_client,
        set_slack_client,
        get_async_slack_client,
        # Formatting utilities
        format_file_info,
        # Error handling utilities
        MIN_API_INTERVAL,
        rate_limit_check,
        make_slack_request,
    )
    from slack_mcp.models import (
        SlackTokenValidation,
        ChannelInfo,
        MessageInfo,
        UserInfo,
        FileUploadInfo,
    )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("slack", description="A comprehensive MCP server for Slack API operations")

# Import and register tools
try:
    from slack_mcp.tools import core as tools_core
    from slack_mcp.tools import message_management as tools_message_mgmt
    from slack_mcp.tools import channel_management as tools_channel_mgmt
    from slack_mcp.tools import user_management as tools_user_mgmt
    from slack_mcp.tools import files as tools_files
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from slack_mcp.tools import core as tools_core
    from slack_mcp.tools import message_management as tools_message_mgmt
    from slack_mcp.tools import channel_management as tools_channel_mgmt
    from slack_mcp.tools import user_management as tools_user_mgmt
    from slack_mcp.tools import files as tools_files

# Register tools from the tools modules
tools_core.register_tools(mcp)
tools_message_mgmt.register_tools(mcp)
tools_channel_mgmt.register_tools(mcp)
tools_user_mgmt.register_tools(mcp)
tools_files.register_tools(mcp)


# Phase 4: Extended Messaging Tools
# Tools moved to slack_mcp.tools.message_management

# Phase 5: Channel Management Tools
# Tools moved to slack_mcp.tools.channel_management

# ========================================
# Phase 6: User Management Tools
# ========================================
# Tools moved to slack_mcp.tools.user_management

def run_server():
    """Run the MCP server for Slack integration."""
    logger.info("Starting Slack MCP server...")
    
    # Try to initialize Slack client from environment
    slack_token = os.getenv('SLACK_BOT_TOKEN')
    if slack_token:
        # Use the client utility function to set the client
        test_client = WebClient(token=slack_token, user_agent_prefix=MCP_USER_AGENT)
        set_slack_client(test_client)
        logger.info("Slack client initialized from environment variable")
    else:
        logger.info("No SLACK_BOT_TOKEN found in environment. Use set_slack_token tool to configure.")
    
    mcp.run(transport='stdio')

if __name__ == "__main__":
    run_server()
