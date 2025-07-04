"""
Client utilities for Slack MCP Server.
Handles Slack client initialization and management.
"""
import os
import logging
from typing import Optional
from slack_sdk import WebClient
from slack_sdk.web.async_client import AsyncWebClient

logger = logging.getLogger(__name__)

# MCP User-Agent for API identification
MCP_USER_AGENT = "Slack-MCP-Server/1.0 (FastMCP)"

# Global variables for Slack clients
_slack_client: Optional[WebClient] = None
_async_slack_client: Optional[AsyncWebClient] = None


def validate_slack_token() -> bool:
    """Validate that Slack client is properly initialized with a token."""
    global _slack_client
    
    if _slack_client is None:
        slack_token = os.getenv('SLACK_BOT_TOKEN')
        if not slack_token:
            raise ValueError(
                "No Slack token found. Please set SLACK_BOT_TOKEN environment variable "
                "or use the set_slack_token tool first."
            )
        _slack_client = WebClient(token=slack_token, user_agent_prefix=MCP_USER_AGENT)
    
    return True


async def init_async_client(token: str = None) -> Optional[AsyncWebClient]:
    """Initialize async Slack client with proper configuration."""
    global _async_slack_client
    
    if token:
        _async_slack_client = AsyncWebClient(
            token=token,
            user_agent_prefix=MCP_USER_AGENT
        )
    elif not _async_slack_client:
        slack_token = os.getenv('SLACK_BOT_TOKEN')
        if slack_token:
            _async_slack_client = AsyncWebClient(
                token=slack_token,
                user_agent_prefix=MCP_USER_AGENT
            )
    
    return _async_slack_client


def get_slack_client() -> Optional[WebClient]:
    """Get the current Slack client instance."""
    return _slack_client


def set_slack_client(client: WebClient) -> None:
    """Set the global Slack client instance."""
    global _slack_client
    _slack_client = client


def get_async_slack_client() -> Optional[AsyncWebClient]:
    """Get the current async Slack client instance."""
    return _async_slack_client
