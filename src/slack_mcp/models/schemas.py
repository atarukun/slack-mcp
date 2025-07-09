"""
Pydantic models for Slack MCP Server.
Defines request/response validation schemas for all tools.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SlackTokenValidation(BaseModel):
    """Model for Slack token validation."""
    token: str = Field(description="Slack bot token (xoxb-*) or user token (xoxp-*)")


class ChannelInfo(BaseModel):
    """Model for channel information requests."""
    channel: str = Field(description="Channel ID or name (e.g., 'C1234567890' or '#general')")


class MessageInfo(BaseModel):
    """Model for message sending requests."""
    channel: str = Field(description="Channel ID or name")
    text: str = Field(description="Message text to send")
    thread_ts: Optional[str] = Field(None, description="Timestamp of parent message to reply in thread")
    blocks: Optional[List[Dict[str, Any]]] = Field(None, description="Slack blocks for rich formatting")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Message attachments")


class UserInfo(BaseModel):
    """Model for user information requests."""
    user: str = Field(description="User ID or email address")


