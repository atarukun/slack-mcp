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
from pydantic import BaseModel, Field
import time
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("slack", description="A comprehensive MCP server for Slack API operations")

# Global variables for Slack clients
slack_client: Optional[WebClient] = None
async_slack_client: Optional[AsyncWebClient] = None

# Rate limiting tracking
last_api_call_time = 0.0
MIN_API_INTERVAL = 1.0  # Minimum seconds between API calls

# MCP User-Agent for API identification
MCP_USER_AGENT = "Slack-MCP-Server/1.0 (FastMCP)"

# Pydantic models for request/response validation
class SlackTokenValidation(BaseModel):
    token: str = Field(description="Slack bot token (xoxb-*) or user token (xoxp-*)")

class ChannelInfo(BaseModel):
    channel: str = Field(description="Channel ID or name (e.g., 'C1234567890' or '#general')")

class MessageInfo(BaseModel):
    channel: str = Field(description="Channel ID or name")
    text: str = Field(description="Message text to send")
    thread_ts: Optional[str] = Field(None, description="Timestamp of parent message to reply in thread")
    blocks: Optional[List[Dict[str, Any]]] = Field(None, description="Slack blocks for rich formatting")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Message attachments")

class UserInfo(BaseModel):
    user: str = Field(description="User ID or email address")

class FileUploadInfo(BaseModel):
    channels: str = Field(description="Comma-separated list of channel IDs or names")
    content: Optional[str] = Field(None, description="File content as text")
    filename: Optional[str] = Field(None, description="Name of the file")
    filetype: Optional[str] = Field(None, description="File type (e.g., 'text', 'json', 'csv')")
    title: Optional[str] = Field(None, description="Title of the file")
    initial_comment: Optional[str] = Field(None, description="Initial comment for the file")

def validate_slack_token() -> bool:
    """Validate that Slack client is properly initialized with a token."""
    global slack_client
    
    if slack_client is None:
        slack_token = os.getenv('SLACK_BOT_TOKEN')
        if not slack_token:
            raise ValueError(
                "No Slack token found. Please set SLACK_BOT_TOKEN environment variable "
                "or use the set_slack_token tool first."
            )
        slack_client = WebClient(token=slack_token, user_agent_prefix=MCP_USER_AGENT)
    
    return True

async def init_async_client(token: str = None) -> Optional[AsyncWebClient]:
    """Initialize async Slack client with proper configuration."""
    global async_slack_client
    
    if token:
        async_slack_client = AsyncWebClient(
            token=token,
            user_agent_prefix=MCP_USER_AGENT
        )
    elif not async_slack_client:
        slack_token = os.getenv('SLACK_BOT_TOKEN')
        if slack_token:
            async_slack_client = AsyncWebClient(
                token=slack_token,
                user_agent_prefix=MCP_USER_AGENT
            )
    
    return async_slack_client

async def rate_limit_check() -> None:
    """Implement rate limiting compliance with async delays."""
    global last_api_call_time
    
    current_time = time.time()
    time_since_last_call = current_time - last_api_call_time
    
    if time_since_last_call < MIN_API_INTERVAL:
        sleep_time = MIN_API_INTERVAL - time_since_last_call
        logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
        await asyncio.sleep(sleep_time)
    
    last_api_call_time = time.time()

async def make_slack_request(client_method, **kwargs) -> Optional[Dict[str, Any]]:
    """Helper function for API requests with error handling and rate limiting."""
    try:
        # Apply rate limiting
        await rate_limit_check()
        
        # Make the API request
        response = await client_method(**kwargs)
        
        if response.get("ok"):
            return response
        else:
            logger.error(f"Slack API error: {response.get('error', 'Unknown error')}")
            return None
            
    except SlackApiError as e:
        logger.error(f"Slack API error: {e.response['error']}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in API request: {str(e)}")
        return None

@mcp.tool("set_slack_token")
def set_slack_token(token: str) -> Dict[str, Any]:
    """
    Set or update the Slack API token for authentication.
    This tool allows you to configure the Slack bot token needed for API operations.
    
    Args:
        token: Slack bot token (xoxb-*) or user token (xoxp-*)
    
    Returns:
        Success message and basic token validation info
    """
    global slack_client
    
    try:
        # Validate token format
        if not token.startswith(('xoxb-', 'xoxp-', 'xoxo-', 'xapp-')):
            return {
                "success": False,
                "error": "Invalid token format. Token should start with 'xoxb-', 'xoxp-', 'xoxo-', or 'xapp-'"
            }
        
        # Initialize client and test connection
        test_client = WebClient(token=token)
        auth_response = test_client.auth_test()
        
        if auth_response["ok"]:
            slack_client = test_client
            return {
                "success": True,
                "message": "Slack token set successfully",
                "bot_id": auth_response.get("bot_id"),
                "user_id": auth_response.get("user_id"),
                "team": auth_response.get("team"),
                "team_id": auth_response.get("team_id")
            }
        else:
            return {
                "success": False,
                "error": f"Token validation failed: {auth_response.get('error', 'Unknown error')}"
            }
            
    except SlackApiError as e:
        return {
            "success": False,
            "error": f"Slack API error: {e.response['error']}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

@mcp.tool("test_slack_connection")
async def test_slack_connection() -> str:
    """
    Test the Slack API connection and return authentication information.
    This tool verifies that the Slack token is valid and includes workspace info retrieval.
    Enhanced with async operations and comprehensive workspace details.
    
    Returns:
        Formatted connection status and authentication details
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Test authentication with rate limiting
        auth_response = await make_slack_request(async_client.auth_test)
        
        if not auth_response:
            return "❌ Authentication failed: No response from Slack API"
        
        # Get additional workspace information
        team_info = await make_slack_request(async_client.team_info)
        
        result = f"✅ **Slack Connection Successful**\n\n"
        result += f"**Authentication Details:**\n"
        result += f"• Bot ID: {auth_response.get('bot_id', 'N/A')}\n"
        result += f"• User ID: {auth_response.get('user_id', 'N/A')}\n"
        result += f"• Team: {auth_response.get('team', 'N/A')}\n"
        result += f"• Team ID: {auth_response.get('team_id', 'N/A')}\n"
        result += f"• Workspace URL: {auth_response.get('url', 'N/A')}\n"
        
        if team_info and team_info.get('team'):
            team_data = team_info['team']
            result += f"\n**Workspace Information:**\n"
            result += f"• Name: {team_data.get('name', 'N/A')}\n"
            result += f"• Domain: {team_data.get('domain', 'N/A')}\n"
            result += f"• Email Domain: {team_data.get('email_domain', 'N/A')}\n"
            result += f"• Icon URL: {team_data.get('icon', {}).get('image_132', 'N/A')}\n"
        
        result += f"\n**API Configuration:**\n"
        result += f"• User-Agent: {MCP_USER_AGENT}\n"
        result += f"• Rate Limiting: {MIN_API_INTERVAL}s minimum interval\n"
        
        return result
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("send_message")
async def send_message(
    channel: str,
    text: str,
    thread_ts: Optional[str] = None,
    blocks: Optional[List[Dict[str, Any]]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Send a message to a Slack channel or user.
    Enhanced with async operations and rate limiting compliance.
    
    Args:
        channel: Channel ID or name (e.g., 'C1234567890', '#general', or '@username')
        text: Message text to send
        thread_ts: Optional timestamp of parent message to reply in thread
        blocks: Optional Slack blocks for rich formatting
        attachments: Optional message attachments
    
    Returns:
        Formatted message sending result
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Send message with rate limiting
        response = await make_slack_request(
            async_client.chat_postMessage,
            channel=channel,
            text=text,
            thread_ts=thread_ts,
            blocks=blocks,
            attachments=attachments
        )
        
        if response:
            result = "✅ **Message Sent Successfully**\n\n"
            result += f"• **Channel:** {response.get('channel', 'N/A')}\n"
            result += f"• **Timestamp:** {response.get('ts', 'N/A')}\n"
            result += f"• **Message:** {text[:100]}{'...' if len(text) > 100 else ''}\n"
            
            if thread_ts:
                result += f"• **Thread Reply:** Yes (parent: {thread_ts})\n"
            
            if blocks:
                result += f"• **Rich Formatting:** {len(blocks)} block(s)\n"
                
            return result
        else:
            return "❌ Failed to send message: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("get_channel_info")
def get_channel_info(channel: str) -> Dict[str, Any]:
    """
    Get detailed information about a Slack channel.
    
    Args:
        channel: Channel ID or name (e.g., 'C1234567890' or '#general')
    
    Returns:
        Channel information including name, topic, purpose, member count, etc.
    """
    try:
        validate_slack_token()
        
        response = slack_client.conversations_info(channel=channel)
        
        if response["ok"]:
            channel_info = response["channel"]
            return {
                "success": True,
                "channel": {
                    "id": channel_info.get("id"),
                    "name": channel_info.get("name"),
                    "is_channel": channel_info.get("is_channel"),
                    "is_group": channel_info.get("is_group"),
                    "is_im": channel_info.get("is_im"),
                    "is_private": channel_info.get("is_private"),
                    "is_archived": channel_info.get("is_archived"),
                    "topic": channel_info.get("topic", {}).get("value"),
                    "purpose": channel_info.get("purpose", {}).get("value"),
                    "num_members": channel_info.get("num_members"),
                    "created": channel_info.get("created")
                }
            }
        else:
            return {
                "success": False,
                "error": f"Failed to get channel info: {response.get('error', 'Unknown error')}"
            }
            
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except SlackApiError as e:
        return {"success": False, "error": f"Slack API error: {e.response['error']}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

@mcp.tool("list_channels")
async def list_channels(types: Optional[str] = "public_channel", limit: int = 100) -> str:
    """
    List channels in the Slack workspace.
    Enhanced with async operations and formatted output.
    
    Args:
        types: Comma-separated list of channel types to include (public_channel, private_channel, mpim, im)
        limit: Maximum number of channels to return (default: 100, max: 1000)
    
    Returns:
        Formatted list of channels with details
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Get channels with rate limiting
        response = await make_slack_request(
            async_client.conversations_list,
            types=types,
            limit=limit
        )
        
        if response:
            channels = response["channels"]
            
            result = f"📋 **Workspace Channels** ({len(channels)} found)\n\n"
            
            # Group channels by type
            public_channels = []
            private_channels = []
            archived_channels = []
            
            for channel in channels:
                channel_data = {
                    "id": channel.get("id"),
                    "name": channel.get("name"),
                    "members": channel.get("num_members", 0),
                    "topic": channel.get("topic", {}).get("value", "No topic"),
                    "purpose": channel.get("purpose", {}).get("value", "No purpose")
                }
                
                if channel.get("is_archived"):
                    archived_channels.append(channel_data)
                elif channel.get("is_private"):
                    private_channels.append(channel_data)
                else:
                    public_channels.append(channel_data)
            
            # Format public channels
            if public_channels:
                result += "**🔓 Public Channels:**\n"
                for ch in public_channels[:10]:  # Limit display
                    result += f"• **#{ch['name']}** ({ch['members']} members)\n"
                    if ch['topic'] and ch['topic'] != "No topic":
                        result += f"  📝 {ch['topic'][:50]}{'...' if len(ch['topic']) > 50 else ''}\n"
                result += "\n"
            
            # Format private channels
            if private_channels:
                result += "**🔒 Private Channels:**\n"
                for ch in private_channels[:5]:  # Limit display
                    result += f"• **{ch['name']}** ({ch['members']} members)\n"
                result += "\n"
            
            # Format archived channels
            if archived_channels:
                result += f"**📦 Archived Channels:** {len(archived_channels)} total\n\n"
            
            result += f"**Summary:**\n"
            result += f"• Public: {len(public_channels)}\n"
            result += f"• Private: {len(private_channels)}\n"
            result += f"• Archived: {len(archived_channels)}\n"
            result += f"• Total: {len(channels)}\n"
            
            return result
        else:
            return "❌ Failed to list channels: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("get_user_info")
def get_user_info(user: str) -> Dict[str, Any]:
    """
    Get information about a Slack user.
    
    Args:
        user: User ID or email address
    
    Returns:
        User information including name, profile details, status, etc.
    """
    try:
        validate_slack_token()
        
        response = slack_client.users_info(user=user)
        
        if response["ok"]:
            user_info = response["user"]
            profile = user_info.get("profile", {})
            
            return {
                "success": True,
                "user": {
                    "id": user_info.get("id"),
                    "name": user_info.get("name"),
                    "real_name": user_info.get("real_name"),
                    "display_name": profile.get("display_name"),
                    "email": profile.get("email"),
                    "phone": profile.get("phone"),
                    "title": profile.get("title"),
                    "status_text": profile.get("status_text"),
                    "status_emoji": profile.get("status_emoji"),
                    "is_admin": user_info.get("is_admin"),
                    "is_bot": user_info.get("is_bot"),
                    "is_app_user": user_info.get("is_app_user"),
                    "updated": user_info.get("updated"),
                    "timezone": user_info.get("tz")
                }
            }
        else:
            return {
                "success": False,
                "error": f"Failed to get user info: {response.get('error', 'Unknown error')}"
            }
            
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except SlackApiError as e:
        return {"success": False, "error": f"Slack API error: {e.response['error']}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

@mcp.tool("upload_file")
def upload_file(
    channels: str,
    content: Optional[str] = None,
    filename: Optional[str] = None,
    filetype: Optional[str] = None,
    title: Optional[str] = None,
    initial_comment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload a file to one or more Slack channels.
    
    Args:
        channels: Comma-separated list of channel IDs or names
        content: File content as text (for text files)
        filename: Name of the file
        filetype: File type (e.g., 'text', 'json', 'csv')
        title: Title of the file
        initial_comment: Initial comment for the file
    
    Returns:
        File upload result with file ID and sharing info
    """
    try:
        validate_slack_token()
        
        if not content:
            return {
                "success": False,
                "error": "File content is required"
            }
        
        response = slack_client.files_upload_v2(
            content=content,
            filename=filename or "file.txt",
            title=title,
            initial_comment=initial_comment,
            channel=channels
        )
        
        if response["ok"]:
            file_info = response["file"]
            return {
                "success": True,
                "message": "File uploaded successfully",
                "file": {
                    "id": file_info.get("id"),
                    "name": file_info.get("name"),
                    "title": file_info.get("title"),
                    "mimetype": file_info.get("mimetype"),
                    "size": file_info.get("size"),
                    "url_private": file_info.get("url_private")
                }
            }
        else:
            return {
                "success": False,
                "error": f"Failed to upload file: {response.get('error', 'Unknown error')}"
            }
            
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except SlackApiError as e:
        return {"success": False, "error": f"Slack API error: {e.response['error']}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

# Phase 4: Extended Messaging Tools

@mcp.tool("update_message")
async def update_message(
    channel: str,
    ts: str,
    text: str,
    blocks: Optional[List[Dict[str, Any]]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Update/edit an existing message in Slack.
    
    Args:
        channel: Channel ID where the message is located
        ts: Timestamp of the message to update
        text: New message text
        blocks: Optional new Slack blocks for rich formatting
        attachments: Optional new message attachments
    
    Returns:
        Formatted update result
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Update message with rate limiting
        response = await make_slack_request(
            async_client.chat_update,
            channel=channel,
            ts=ts,
            text=text,
            blocks=blocks,
            attachments=attachments
        )
        
        if response:
            result = "✅ **Message Updated Successfully**\n\n"
            result += f"• **Channel:** {response.get('channel', 'N/A')}\n"
            result += f"• **Timestamp:** {response.get('ts', 'N/A')}\n"
            result += f"• **New Text:** {text[:100]}{'...' if len(text) > 100 else ''}\n"
            
            if blocks:
                result += f"• **Rich Formatting:** {len(blocks)} block(s)\n"
                
            return result
        else:
            return "❌ Failed to update message: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("delete_message")
async def delete_message(channel: str, ts: str) -> str:
    """
    Delete a message from Slack.
    
    Args:
        channel: Channel ID where the message is located
        ts: Timestamp of the message to delete
    
    Returns:
        Formatted deletion result
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Delete message with rate limiting
        response = await make_slack_request(
            async_client.chat_delete,
            channel=channel,
            ts=ts
        )
        
        if response:
            result = "✅ **Message Deleted Successfully**\n\n"
            result += f"• **Channel:** {response.get('channel', 'N/A')}\n"
            result += f"• **Timestamp:** {response.get('ts', 'N/A')}\n"
            
            return result
        else:
            return "❌ Failed to delete message: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("pin_message")
async def pin_message(channel: str, timestamp: str) -> str:
    """
    Pin a message to a Slack channel.
    
    Args:
        channel: Channel ID where the message is located
        timestamp: Timestamp of the message to pin
    
    Returns:
        Formatted pin result
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Pin message with rate limiting
        response = await make_slack_request(
            async_client.pins_add,
            channel=channel,
            timestamp=timestamp
        )
        
        if response:
            result = "✅ **Message Pinned Successfully**\n\n"
            result += f"• **Channel:** {channel}\n"
            result += f"• **Message Timestamp:** {timestamp}\n"
            
            return result
        else:
            return "❌ Failed to pin message: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("unpin_message")
async def unpin_message(channel: str, timestamp: str) -> str:
    """
    Unpin a message from a Slack channel.
    
    Args:
        channel: Channel ID where the message is located
        timestamp: Timestamp of the message to unpin
    
    Returns:
        Formatted unpin result
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Unpin message with rate limiting
        response = await make_slack_request(
            async_client.pins_remove,
            channel=channel,
            timestamp=timestamp
        )
        
        if response:
            result = "✅ **Message Unpinned Successfully**\n\n"
            result += f"• **Channel:** {channel}\n"
            result += f"• **Message Timestamp:** {timestamp}\n"
            
            return result
        else:
            return "❌ Failed to unpin message: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("get_message_permalink")
async def get_message_permalink(channel: str, message_ts: str) -> str:
    """
    Get a permalink URL for a specific message.
    
    Args:
        channel: Channel ID where the message is located
        message_ts: Timestamp of the message
    
    Returns:
        Formatted permalink information
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Get permalink with rate limiting
        response = await make_slack_request(
            async_client.chat_getPermalink,
            channel=channel,
            message_ts=message_ts
        )
        
        if response:
            result = "✅ **Permalink Generated Successfully**\n\n"
            result += f"• **Channel:** {channel}\n"
            result += f"• **Message Timestamp:** {message_ts}\n"
            result += f"• **Permalink:** {response.get('permalink', 'N/A')}\n"
            
            return result
        else:
            return "❌ Failed to get permalink: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("schedule_message")
async def schedule_message(
    channel: str,
    text: str,
    post_at: int,
    blocks: Optional[List[Dict[str, Any]]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Schedule a message to be sent at a specific time.
    
    Args:
        channel: Channel ID or name to send the message to
        text: Message text to send
        post_at: Unix timestamp when the message should be sent
        blocks: Optional Slack blocks for rich formatting
        attachments: Optional message attachments
    
    Returns:
        Formatted scheduling result
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Apply rate limiting first
        await rate_limit_check()
        
        # Make direct API call with enhanced error handling
        try:
            response = await async_client.chat_scheduleMessage(
                channel=channel,
                text=text,
                post_at=post_at,
                blocks=blocks,
                attachments=attachments
            )
            
            if response.get("ok"):
                scheduled_time = datetime.fromtimestamp(post_at).strftime('%Y-%m-%d %H:%M:%S UTC')
                
                result = "✅ **Message Scheduled Successfully**\n\n"
                result += f"• **Channel:** {response.get('channel', 'N/A')}\n"
                result += f"• **Scheduled Message ID:** {response.get('scheduled_message_id', 'N/A')}\n"
                result += f"• **Post Time:** {scheduled_time}\n"
                result += f"• **Message:** {text[:100]}{'...' if len(text) > 100 else ''}\n"
                
                if blocks:
                    result += f"• **Rich Formatting:** {len(blocks)} block(s)\n"
                    
                return result
            else:
                error_msg = response.get('error', 'Unknown error')
                return f"❌ Failed to schedule message: {error_msg}\n\nFull response: {response}"
                
        except SlackApiError as api_error:
            error_detail = api_error.response.get('error', 'Unknown API error')
            return f"❌ Slack API Error in scheduling: {error_detail}\n\nDetails: {api_error.response}"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("get_thread_replies")
async def get_thread_replies(channel: str, thread_ts: str, limit: int = 10) -> str:
    """
    Get replies from a message thread.
    
    Args:
        channel: Channel ID where the thread is located
        thread_ts: Timestamp of the parent message
        limit: Maximum number of replies to return (default: 10, max: 1000)
    
    Returns:
        Formatted thread replies information
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Get thread replies with rate limiting
        response = await make_slack_request(
            async_client.conversations_replies,
            channel=channel,
            ts=thread_ts,
            limit=limit
        )
        
        if response:
            messages = response.get('messages', [])
            
            result = f"🧵 **Thread Replies** ({len(messages)} messages)\n\n"
            
            if messages:
                # First message is the parent
                parent = messages[0]
                result += f"**📝 Parent Message:**\n"
                result += f"• **User:** <@{parent.get('user', 'Unknown')}>\n"
                result += f"• **Time:** {datetime.fromtimestamp(float(parent.get('ts', 0))).strftime('%Y-%m-%d %H:%M:%S')}\n"
                result += f"• **Text:** {parent.get('text', 'No text')[:150]}{'...' if len(parent.get('text', '')) > 150 else ''}\n\n"
                
                # Show replies
                if len(messages) > 1:
                    result += f"**💬 Replies ({len(messages) - 1}):**\n"
                    for i, reply in enumerate(messages[1:], 1):
                        result += f"\n**{i}.** <@{reply.get('user', 'Unknown')}>\n"
                        result += f"   📅 {datetime.fromtimestamp(float(reply.get('ts', 0))).strftime('%Y-%m-%d %H:%M:%S')}\n"
                        result += f"   💭 {reply.get('text', 'No text')[:100]}{'...' if len(reply.get('text', '')) > 100 else ''}\n"
                else:
                    result += "**💬 No replies yet**\n"
            else:
                result += "❌ No messages found in thread\n"
            
            return result
        else:
            return "❌ Failed to get thread replies: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("send_direct_message")
async def send_direct_message(
    user: str,
    text: str,
    blocks: Optional[List[Dict[str, Any]]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Send a direct message to a specific user.
    
    Args:
        user: User ID or email address to send the message to
        text: Message text to send
        blocks: Optional Slack blocks for rich formatting
        attachments: Optional message attachments
    
    Returns:
        Formatted direct message result
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # First, open a direct message conversation
        dm_response = await make_slack_request(
            async_client.conversations_open,
            users=user
        )
        
        if not dm_response:
            return "❌ Failed to open direct message conversation"
        
        dm_channel = dm_response.get('channel', {}).get('id')
        if not dm_channel:
            return "❌ Failed to get direct message channel ID"
        
        # Send message to the DM channel
        response = await make_slack_request(
            async_client.chat_postMessage,
            channel=dm_channel,
            text=text,
            blocks=blocks,
            attachments=attachments
        )
        
        if response:
            result = "✅ **Direct Message Sent Successfully**\n\n"
            result += f"• **Recipient:** <@{user}>\n"
            result += f"• **DM Channel:** {dm_channel}\n"
            result += f"• **Timestamp:** {response.get('ts', 'N/A')}\n"
            result += f"• **Message:** {text[:100]}{'...' if len(text) > 100 else ''}\n"
            
            if blocks:
                result += f"• **Rich Formatting:** {len(blocks)} block(s)\n"
                
            return result
        else:
            return "❌ Failed to send direct message: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

# Phase 5: Channel Management Tools

@mcp.tool("create_channel")
async def create_channel(
    name: str,
    is_private: bool = False,
    description: Optional[str] = None,
    team_id: Optional[str] = None
) -> str:
    """
    Create a new Slack channel.
    
    Args:
        name: Name for the new channel (lowercase, no spaces or periods)
        is_private: Whether to create a private channel (default: False)
        description: Optional description/purpose for the channel
        team_id: Optional team ID for enterprise grid workspaces
    
    Returns:
        Formatted channel creation result
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Create channel with rate limiting
        response = await make_slack_request(
            async_client.conversations_create,
            name=name,
            is_private=is_private,
            team_id=team_id
        )
        
        if response:
            channel = response.get('channel', {})
            
            result = "✅ **Channel Created Successfully**\n\n"
            result += f"• **Name:** #{channel.get('name', 'N/A')}\n"
            result += f"• **ID:** {channel.get('id', 'N/A')}\n"
            result += f"• **Type:** {'Private' if is_private else 'Public'} Channel\n"
            result += f"• **Creator:** <@{channel.get('creator', 'N/A')}>\n"
            result += f"• **Created:** {datetime.fromtimestamp(channel.get('created', 0)).strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # Set description if provided
            if description and channel.get('id'):
                purpose_response = await make_slack_request(
                    async_client.conversations_setPurpose,
                    channel=channel['id'],
                    purpose=description
                )
                if purpose_response:
                    result += f"• **Purpose:** {description}\n"
            
            return result
        else:
            return "❌ Failed to create channel: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("archive_channel")
async def archive_channel(channel: str) -> str:
    """
    Archive a Slack channel.
    
    Args:
        channel: Channel ID to archive
    
    Returns:
        Formatted archive result
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Archive channel with rate limiting
        response = await make_slack_request(
            async_client.conversations_archive,
            channel=channel
        )
        
        if response:
            result = "✅ **Channel Archived Successfully**\n\n"
            result += f"• **Channel ID:** {channel}\n"
            result += f"• **Status:** Archived\n"
            result += "• **Note:** Archived channels can be unarchived if needed\n"
            
            return result
        else:
            return "❌ Failed to archive channel: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("unarchive_channel")
async def unarchive_channel(channel: str) -> str:
    """
    Unarchive a previously archived Slack channel.
    
    Args:
        channel: Channel ID to unarchive
    
    Returns:
        Formatted unarchive result
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Unarchive channel with rate limiting
        response = await make_slack_request(
            async_client.conversations_unarchive,
            channel=channel
        )
        
        if response:
            result = "✅ **Channel Unarchived Successfully**\n\n"
            result += f"• **Channel ID:** {channel}\n"
            result += f"• **Status:** Active\n"
            result += "• **Note:** Channel is now available for messages\n"
            
            return result
        else:
            return "❌ Failed to unarchive channel: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("set_channel_topic")
async def set_channel_topic(channel: str, topic: str) -> str:
    """
    Set or update a channel's topic.
    
    Args:
        channel: Channel ID to update
        topic: New topic for the channel
    
    Returns:
        Formatted topic update result
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Set topic with rate limiting
        response = await make_slack_request(
            async_client.conversations_setTopic,
            channel=channel,
            topic=topic
        )
        
        if response:
            result = "✅ **Channel Topic Updated Successfully**\n\n"
            result += f"• **Channel:** {channel}\n"
            result += f"• **New Topic:** {topic}\n"
            
            return result
        else:
            return "❌ Failed to set channel topic: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("set_channel_purpose")
async def set_channel_purpose(channel: str, purpose: str) -> str:
    """
    Set or update a channel's purpose/description.
    
    Args:
        channel: Channel ID to update
        purpose: New purpose/description for the channel
    
    Returns:
        Formatted purpose update result
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Set purpose with rate limiting
        response = await make_slack_request(
            async_client.conversations_setPurpose,
            channel=channel,
            purpose=purpose
        )
        
        if response:
            result = "✅ **Channel Purpose Updated Successfully**\n\n"
            result += f"• **Channel:** {channel}\n"
            result += f"• **New Purpose:** {purpose}\n"
            
            return result
        else:
            return "❌ Failed to set channel purpose: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("join_channel")
async def join_channel(channel: str) -> str:
    """
    Join a public channel.
    
    Args:
        channel: Channel ID to join
    
    Returns:
        Formatted join result
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Join channel with rate limiting
        response = await make_slack_request(
            async_client.conversations_join,
            channel=channel
        )
        
        if response:
            channel_info = response.get('channel', {})
            
            result = "✅ **Successfully Joined Channel**\n\n"
            result += f"• **Channel Name:** #{channel_info.get('name', 'N/A')}\n"
            result += f"• **Channel ID:** {channel_info.get('id', 'N/A')}\n"
            result += f"• **Members:** {channel_info.get('num_members', 'N/A')}\n"
            
            if channel_info.get('topic', {}).get('value'):
                result += f"• **Topic:** {channel_info['topic']['value']}\n"
            
            return result
        else:
            return "❌ Failed to join channel: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("leave_channel")
async def leave_channel(channel: str) -> str:
    """
    Leave a channel.
    
    Args:
        channel: Channel ID to leave
    
    Returns:
        Formatted leave result
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Leave channel with rate limiting
        response = await make_slack_request(
            async_client.conversations_leave,
            channel=channel
        )
        
        if response:
            result = "✅ **Successfully Left Channel**\n\n"
            result += f"• **Channel ID:** {channel}\n"
            result += "• **Status:** No longer a member\n"
            
            return result
        else:
            return "❌ Failed to leave channel: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("invite_to_channel")
async def invite_to_channel(channel: str, users: str) -> str:
    """
    Invite one or more users to a channel.
    
    Args:
        channel: Channel ID to invite users to
        users: Comma-separated list of user IDs to invite
    
    Returns:
        Formatted invitation result
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Invite users with rate limiting
        response = await make_slack_request(
            async_client.conversations_invite,
            channel=channel,
            users=users
        )
        
        if response:
            channel_info = response.get('channel', {})
            user_list = users.split(',')
            
            result = "✅ **Users Invited Successfully**\n\n"
            result += f"• **Channel:** #{channel_info.get('name', 'N/A')} ({channel})\n"
            result += f"• **Invited Users:** {len(user_list)}\n"
            
            for user_id in user_list:
                result += f"  - <@{user_id.strip()}>\n"
            
            result += f"• **Total Members:** {channel_info.get('num_members', 'N/A')}\n"
            
            return result
        else:
            return "❌ Failed to invite users: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("remove_from_channel")
async def remove_from_channel(channel: str, user: str) -> str:
    """
    Remove a user from a channel (kick).
    
    Args:
        channel: Channel ID to remove user from
        user: User ID to remove
    
    Returns:
        Formatted removal result
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Remove user with rate limiting
        response = await make_slack_request(
            async_client.conversations_kick,
            channel=channel,
            user=user
        )
        
        if response:
            result = "✅ **User Removed Successfully**\n\n"
            result += f"• **Channel:** {channel}\n"
            result += f"• **Removed User:** <@{user}>\n"
            result += "• **Status:** User is no longer a member\n"
            
            return result
        else:
            return "❌ Failed to remove user: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("list_channel_members")
async def list_channel_members(channel: str, limit: int = 100) -> str:
    """
    List members of a channel.
    
    Args:
        channel: Channel ID to get members for
        limit: Maximum number of members to return (default: 100)
    
    Returns:
        Formatted list of channel members
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Get members with rate limiting
        response = await make_slack_request(
            async_client.conversations_members,
            channel=channel,
            limit=limit
        )
        
        if response:
            members = response.get('members', [])
            
            result = f"👥 **Channel Members** ({len(members)} total)\n\n"
            result += f"• **Channel ID:** {channel}\n\n"
            
            # Get channel info for name
            channel_info_response = await make_slack_request(
                async_client.conversations_info,
                channel=channel
            )
            
            if channel_info_response:
                channel_name = channel_info_response.get('channel', {}).get('name', 'Unknown')
                result = f"👥 **Channel Members for #{channel_name}** ({len(members)} total)\n\n"
            
            result += "**Members:**\n"
            for i, member_id in enumerate(members[:20], 1):  # Show first 20
                result += f"{i}. <@{member_id}>\n"
            
            if len(members) > 20:
                result += f"\n... and {len(members) - 20} more members\n"
            
            return result
        else:
            return "❌ Failed to list channel members: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

def run_server():
    """Run the MCP server for Slack integration."""
    logger.info("Starting Slack MCP server...")
    
    # Try to initialize Slack client from environment
    slack_token = os.getenv('SLACK_BOT_TOKEN')
    if slack_token:
        global slack_client
        slack_client = WebClient(token=slack_token)
        logger.info("Slack client initialized from environment variable")
    else:
        logger.info("No SLACK_BOT_TOKEN found in environment. Use set_slack_token tool to configure.")
    
    mcp.run(transport='stdio')

if __name__ == "__main__":
    run_server()
