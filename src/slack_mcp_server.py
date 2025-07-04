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
async def get_channel_info(channel: str) -> str:
    """
    Get detailed information about a Slack channel.
    
    Args:
        channel: Channel ID or name (e.g., 'C1234567890' or '#general')
    
    Returns:
        Channel information including name, topic, purpose, member count, etc.
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Get channel info with rate limiting
        response = await make_slack_request(
            async_client.conversations_info,
            channel=channel
        )
        
        if response:
            channel_info = response["channel"]
            
            # Determine channel type
            if channel_info.get("is_im"):
                channel_type = "Direct Message"
                icon = "💬"
            elif channel_info.get("is_mpim"):
                channel_type = "Group Direct Message"
                icon = "👥"
            elif channel_info.get("is_private"):
                channel_type = "Private Channel"
                icon = "🔒"
            else:
                channel_type = "Public Channel"
                icon = "📢"
            
            result = f"{icon} **Channel Information**\n\n"
            result += f"• **Name:** #{channel_info.get('name', 'N/A')}\n"
            result += f"• **ID:** {channel_info.get('id', 'N/A')}\n"
            result += f"• **Type:** {channel_type}\n"
            
            if channel_info.get("is_archived"):
                result += f"• **Status:** 📦 Archived\n"
            
            if channel_info.get("num_members") is not None:
                result += f"• **Members:** {channel_info['num_members']}\n"
            
            # Creation date
            if channel_info.get("created"):
                created_date = datetime.fromtimestamp(channel_info["created"]).strftime('%Y-%m-%d %H:%M:%S')
                result += f"• **Created:** {created_date}\n"
            
            # Topic
            topic = channel_info.get("topic", {}).get("value")
            if topic:
                result += f"\n• **Topic:** {topic}\n"
            
            # Purpose
            purpose = channel_info.get("purpose", {}).get("value")
            if purpose:
                result += f"• **Purpose:** {purpose}\n"
            
            # Creator
            if channel_info.get("creator"):
                result += f"\n• **Created by:** <@{channel_info['creator']}>\n"
            
            # Additional metadata for private channels
            if channel_info.get("is_private") and channel_info.get("is_member") is not None:
                result += f"• **You are a member:** {'Yes' if channel_info['is_member'] else 'No'}\n"
            
            return result
        else:
            return "❌ Failed to get channel info: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

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


@mcp.tool("upload_file")
async def upload_file(
    channels: str,
    content: Optional[str] = None,
    filename: Optional[str] = None,
    filetype: Optional[str] = None,
    title: Optional[str] = None,
    initial_comment: Optional[str] = None
) -> str:
    """
    Upload a file to one or more Slack channels or users.
    
    Args:
        channels: Comma-separated list of channel IDs, channel names, or user IDs
        content: File content as text (for text files)
        filename: Name of the file
        filetype: File type (e.g., 'text', 'json', 'csv', 'python', 'javascript')
        title: Title of the file
        initial_comment: Initial comment for the file
    
    Returns:
        File upload result with file ID and sharing info
    """
    try:
        validate_slack_token()
        
        if not content:
            return "❌ File content is required"
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Use files_upload_v2 with rate limiting
        response = await make_slack_request(
            async_client.files_upload_v2,
            content=content,
            filename=filename or "file.txt",
            title=title,
            initial_comment=initial_comment,
            channel=channels
        )
        
        if response:
            file_info = response["file"]
            
            result = "✅ **File Uploaded Successfully**\n\n"
            result += f"• **File ID:** {file_info.get('id', 'N/A')}\n"
            result += f"• **Name:** {file_info.get('name', 'N/A')}\n"
            
            if file_info.get('title'):
                result += f"• **Title:** {file_info['title']}\n"
            
            # File size formatting
            if file_info.get('size'):
                size = file_info['size']
                if size < 1024:
                    size_str = f"{size} bytes"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                result += f"• **Size:** {size_str}\n"
            
            if file_info.get('mimetype'):
                result += f"• **Type:** {file_info['mimetype']}\n"
            elif filetype:
                result += f"• **Type:** {filetype}\n"
            
            # Channels the file was shared to
            result += f"\n• **Shared to:** {channels}\n"
            
            if initial_comment:
                result += f"• **Comment:** {initial_comment}\n"
            
            # File URLs
            if file_info.get('url_private'):
                result += f"\n• **URL:** {file_info['url_private']}\n"
            
            if file_info.get('permalink'):
                result += f"• **Permalink:** {file_info['permalink']}\n"
            
            # Upload timestamp
            if file_info.get('created'):
                upload_time = datetime.fromtimestamp(file_info['created']).strftime('%Y-%m-%d %H:%M:%S')
                result += f"\n• **Uploaded at:** {upload_time}\n"
            
            return result
        else:
            return "❌ Failed to upload file: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("upload_file_to_user")
async def upload_file_to_user(
    user: str,
    content: str,
    filename: Optional[str] = None,
    filetype: Optional[str] = None,
    title: Optional[str] = None,
    initial_comment: Optional[str] = None
) -> str:
    """
    Upload a file directly to a user via direct message.
    
    Args:
        user: User ID or email address to send the file to
        content: File content as text
        filename: Name of the file
        filetype: File type (e.g., 'text', 'json', 'csv')
        title: Title of the file
        initial_comment: Initial comment for the file
    
    Returns:
        File upload result with details
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # First, open a DM with the user if needed
        dm_response = await make_slack_request(
            async_client.conversations_open,
            users=user
        )
        
        if not dm_response:
            return "❌ Failed to open direct message with user"
        
        dm_channel = dm_response.get('channel', {}).get('id')
        if not dm_channel:
            return "❌ Could not get DM channel ID"
        
        # Upload file to the DM channel
        response = await make_slack_request(
            async_client.files_upload_v2,
            content=content,
            filename=filename or "file.txt",
            title=title,
            initial_comment=initial_comment,
            channel=dm_channel
        )
        
        if response:
            file_info = response["file"]
            
            result = "✅ **File Uploaded to User Successfully**\n\n"
            result += f"• **Recipient:** <@{user}>\n"
            result += f"• **File ID:** {file_info.get('id', 'N/A')}\n"
            result += f"• **Name:** {file_info.get('name', 'N/A')}\n"
            
            if file_info.get('title'):
                result += f"• **Title:** {file_info['title']}\n"
            
            # File size formatting
            if file_info.get('size'):
                size = file_info['size']
                if size < 1024:
                    size_str = f"{size} bytes"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                result += f"• **Size:** {size_str}\n"
            
            if initial_comment:
                result += f"\n• **Comment:** {initial_comment}\n"
            
            if file_info.get('permalink'):
                result += f"\n• **Permalink:** {file_info['permalink']}\n"
            
            return result
        else:
            return "❌ Failed to upload file to user: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("get_file_content")
async def get_file_content(file_id: str, max_size_mb: float = 10.0) -> str:
    """
    Get the content of a text file from Slack (download functionality).
    
    Args:
        file_id: The ID of the file to download
        max_size_mb: Maximum file size to download in MB (default: 10MB)
    
    Returns:
        The file content or error message
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Get file info first
        info_response = await make_slack_request(
            async_client.files_info,
            file=file_id
        )
        
        if not info_response:
            return "❌ File not found or inaccessible"
        
        file_info = info_response.get('file', {})
        file_name = file_info.get('name', 'Unknown')
        file_size = file_info.get('size', 0)
        mimetype = file_info.get('mimetype', '')
        
        # Check file size
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            return f"❌ File too large: {file_size / (1024 * 1024):.1f}MB exceeds {max_size_mb}MB limit"
        
        # Check if it's a text-based file
        text_mimetypes = ['text/', 'application/json', 'application/xml', 'application/javascript', 
                         'application/x-yaml', 'application/x-python', 'application/x-sh']
        
        is_text_file = any(mimetype.startswith(mt) for mt in text_mimetypes)
        
        if not is_text_file and not file_info.get('filetype') in ['text', 'json', 'xml', 'yaml', 'python', 'javascript', 'sh', 'bash']:
            return f"❌ File appears to be binary (MIME: {mimetype}). This tool only supports text files."
        
        # Get download URL
        download_url = file_info.get('url_private_download')
        if not download_url:
            return "❌ No download URL available for this file"
        
        # Download the file content
        import httpx
        headers = {
            'Authorization': f'Bearer {async_client.token}',
            'User-Agent': MCP_USER_AGENT
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(download_url, headers=headers)
            
            if response.status_code == 200:
                content = response.text
                
                result = f"📄 **File Content Retrieved**\n\n"
                result += f"**File:** {file_name} (ID: {file_id})\n"
                result += f"**Size:** {len(content)} characters\n"
                result += f"**Type:** {mimetype or file_info.get('filetype', 'unknown')}\n\n"
                result += "**Content:**\n```\n"
                
                # Limit displayed content if too long
                if len(content) > 50000:
                    result += content[:50000]
                    result += "\n... (content truncated at 50,000 characters)\n"
                else:
                    result += content
                
                result += "\n```"
                return result
            else:
                return f"❌ Failed to download file: HTTP {response.status_code}"
                
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

# Phase 7: File Operations (Enhanced)

@mcp.tool("list_files")
async def list_files(
    channel: Optional[str] = None,
    user: Optional[str] = None,
    types: Optional[str] = None,
    count: int = 20,
    page: int = 1
) -> str:
    """
    List files in the Slack workspace with optional filtering.
    
    Args:
        channel: Channel ID to filter files from
        user: User ID to filter files uploaded by
        types: Comma-separated list of file types (e.g., 'images,pdfs,zips')
        count: Number of files to return per page (default: 20, max: 100)
        page: Page number of results to return (default: 1)
    
    Returns:
        Formatted list of files with details
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Build request parameters
        params = {
            "count": min(count, 100),  # Cap at 100
            "page": page
        }
        
        if channel:
            params["channel"] = channel
        if user:
            params["user"] = user
        if types:
            params["types"] = types
        
        # List files with rate limiting
        response = await make_slack_request(
            async_client.files_list,
            **params
        )
        
        if response:
            files = response.get('files', [])
            total = response.get('paging', {}).get('total', 0)
            pages = response.get('paging', {}).get('pages', 1)
            current_page = response.get('paging', {}).get('page', 1)
            
            result = f"📁 **Files in Workspace** (Page {current_page}/{pages}, Total: {total})\n\n"
            
            if not files:
                result += "No files found matching the criteria.\n"
                return result
            
            # Group files by type
            images = []
            documents = []
            videos = []
            other = []
            
            for file in files:
                if file.get('mimetype', '').startswith('image/'):
                    images.append(file)
                elif file.get('mimetype', '').startswith(('text/', 'application/pdf', 'application/msword', 'application/vnd.')):
                    documents.append(file)
                elif file.get('mimetype', '').startswith('video/'):
                    videos.append(file)
                else:
                    other.append(file)
            
            # Format file listings by type
            if images:
                result += f"**🖼️ Images ({len(images)}):**\n"
                for i, file in enumerate(images[:5], 1):
                    result += format_file_info(file, i)
                if len(images) > 5:
                    result += f"... and {len(images) - 5} more images\n"
                result += "\n"
            
            if documents:
                result += f"**📄 Documents ({len(documents)}):**\n"
                for i, file in enumerate(documents[:5], 1):
                    result += format_file_info(file, i)
                if len(documents) > 5:
                    result += f"... and {len(documents) - 5} more documents\n"
                result += "\n"
            
            if videos:
                result += f"**🎥 Videos ({len(videos)}):**\n"
                for i, file in enumerate(videos[:3], 1):
                    result += format_file_info(file, i)
                if len(videos) > 3:
                    result += f"... and {len(videos) - 3} more videos\n"
                result += "\n"
            
            if other:
                result += f"**📎 Other Files ({len(other)}):**\n"
                for i, file in enumerate(other[:5], 1):
                    result += format_file_info(file, i)
                if len(other) > 5:
                    result += f"... and {len(other) - 5} more files\n"
                result += "\n"
            
            # Add pagination info
            if pages > 1:
                result += f"\n**Navigation:** Page {current_page} of {pages}\n"
                if current_page > 1:
                    result += f"• Previous page: use page={current_page - 1}\n"
                if current_page < pages:
                    result += f"• Next page: use page={current_page + 1}\n"
            
            return result
        else:
            return "❌ Failed to list files: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

def format_file_info(file: Dict[str, Any], index: int) -> str:
    """Helper function to format file information."""
    result = f"{index}. **{file.get('name', 'Unnamed')}**\n"
    result += f"   • ID: {file.get('id', 'N/A')}\n"
    
    # File size
    if file.get('size'):
        size = file['size']
        if size < 1024:
            size_str = f"{size} bytes"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        result += f"   • Size: {size_str}\n"
    
    # Upload info
    if file.get('user'):
        result += f"   • Uploaded by: <@{file['user']}>\n"
    if file.get('created'):
        upload_time = datetime.fromtimestamp(file['created']).strftime('%Y-%m-%d %H:%M')
        result += f"   • Uploaded: {upload_time}\n"
    
    # Channels shared to
    if file.get('channels'):
        result += f"   • Shared in: {len(file['channels'])} channel(s)\n"
    
    return result

@mcp.tool("get_file_info")
async def get_file_info(file_id: str) -> str:
    """
    Get detailed information about a specific file.
    
    Args:
        file_id: The ID of the file to get information about
    
    Returns:
        Detailed file information including metadata and sharing details
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Get file info with rate limiting
        response = await make_slack_request(
            async_client.files_info,
            file=file_id
        )
        
        if response:
            file = response.get('file', {})
            
            result = f"📄 **File Information**\n\n"
            result += f"**Basic Info:**\n"
            result += f"• **Name:** {file.get('name', 'Unnamed')}\n"
            result += f"• **ID:** {file.get('id', 'N/A')}\n"
            
            if file.get('title'):
                result += f"• **Title:** {file['title']}\n"
            
            # File type and size
            result += f"\n**File Details:**\n"
            if file.get('mimetype'):
                result += f"• **MIME Type:** {file['mimetype']}\n"
            if file.get('filetype'):
                result += f"• **File Type:** {file['filetype']}\n"
            
            if file.get('size'):
                size = file['size']
                if size < 1024:
                    size_str = f"{size} bytes"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                result += f"• **Size:** {size_str}\n"
            
            # Upload information
            result += f"\n**Upload Info:**\n"
            if file.get('user'):
                result += f"• **Uploaded by:** <@{file['user']}>\n"
            if file.get('created'):
                upload_time = datetime.fromtimestamp(file['created']).strftime('%Y-%m-%d %H:%M:%S')
                result += f"• **Upload Time:** {upload_time}\n"
            
            # Image/video specific info
            if file.get('original_w') and file.get('original_h'):
                result += f"\n**Media Info:**\n"
                result += f"• **Dimensions:** {file['original_w']}x{file['original_h']} pixels\n"
            
            # Sharing information
            result += f"\n**Sharing:**\n"
            if file.get('channels'):
                result += f"• **Public Channels:** {', '.join([f'<#{ch}>' for ch in file['channels']])}\n"
            if file.get('groups'):
                result += f"• **Private Channels:** {len(file['groups'])} channel(s)\n"
            if file.get('ims'):
                result += f"• **Direct Messages:** {len(file['ims'])} conversation(s)\n"
            
            # URLs
            result += f"\n**Access URLs:**\n"
            if file.get('url_private'):
                result += f"• **Private URL:** {file['url_private']}\n"
            if file.get('permalink'):
                result += f"• **Permalink:** {file['permalink']}\n"
            if file.get('url_private_download'):
                result += f"• **Download URL:** {file['url_private_download']}\n"
            
            # Comments
            if file.get('initial_comment'):
                result += f"\n**Initial Comment:**\n{file['initial_comment'].get('comment', 'No comment')}\n"
            
            if file.get('comments_count', 0) > 0:
                result += f"\n• **Total Comments:** {file['comments_count']}\n"
            
            return result
        else:
            return "❌ Failed to get file info: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("delete_file")
async def delete_file(file_id: str) -> str:
    """
    Delete a file from Slack.
    
    Args:
        file_id: The ID of the file to delete
    
    Returns:
        Confirmation of file deletion
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # First, get file info for confirmation
        info_response = await make_slack_request(
            async_client.files_info,
            file=file_id
        )
        
        if not info_response:
            return "❌ File not found or inaccessible"
        
        file_name = info_response.get('file', {}).get('name', 'Unknown')
        
        # Delete file with rate limiting
        response = await make_slack_request(
            async_client.files_delete,
            file=file_id
        )
        
        if response:
            result = f"✅ **File Deleted Successfully**\n\n"
            result += f"• **File Name:** {file_name}\n"
            result += f"• **File ID:** {file_id}\n"
            result += f"• **Status:** Permanently deleted\n"
            return result
        else:
            return "❌ Failed to delete file: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("share_file")
async def share_file(
    file_id: str,
    channels: str,
    comment: Optional[str] = None
) -> str:
    """
    Share an existing file to additional channels.
    
    Args:
        file_id: The ID of the file to share
        channels: Comma-separated list of channel IDs to share the file with
        comment: Optional comment to include when sharing
    
    Returns:
        Confirmation of file sharing with details
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Get file info first
        info_response = await make_slack_request(
            async_client.files_info,
            file=file_id
        )
        
        if not info_response:
            return "❌ File not found or inaccessible"
        
        file_info = info_response.get('file', {})
        file_name = file_info.get('name', 'Unknown')
        
        # Share file using files.sharedPublicURL for each channel
        # Note: Slack API doesn't have a direct "share to channel" endpoint,
        # so we'll use the message with file sharing approach
        channel_list = [ch.strip() for ch in channels.split(',')]
        shared_to = []
        failed = []
        
        for channel in channel_list:
            try:
                # Send a message with the file shared
                msg_params = {
                    "channel": channel,
                    "text": comment or f"Shared file: {file_name}",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": comment or f"Shared file: *{file_name}*"
                            }
                        }
                    ]
                }
                
                # If the file has a permalink, include it
                if file_info.get('permalink'):
                    msg_params["blocks"].append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"<{file_info['permalink']}|View File>"
                        }
                    })
                
                response = await make_slack_request(
                    async_client.chat_postMessage,
                    **msg_params
                )
                
                if response:
                    shared_to.append(channel)
                else:
                    failed.append(channel)
                    
            except Exception as e:
                logger.error(f"Failed to share to {channel}: {str(e)}")
                failed.append(channel)
        
        # Format result
        result = f"📤 **File Sharing Results**\n\n"
        result += f"**File:** {file_name} (ID: {file_id})\n\n"
        
        if shared_to:
            result += f"✅ **Successfully shared to:**\n"
            for ch in shared_to:
                result += f"• <#{ch}>\n"
        
        if failed:
            result += f"\n❌ **Failed to share to:**\n"
            for ch in failed:
                result += f"• {ch}\n"
        
        if comment:
            result += f"\n**Comment:** {comment}\n"
        
        return result
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

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

# ========================================
# Phase 6: User Management Tools
# ========================================

@mcp.tool("get_user_info")
async def get_user_info(user: str) -> str:
    """
    Get information about a Slack user.
    
    Args:
        user: User ID or email address
    
    Returns:
        User information including name, profile details, status, etc.
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Get user info with rate limiting
        response = await make_slack_request(
            async_client.users_info,
            user=user
        )
        
        if response:
            user_data = response.get('user', {})
            profile = user_data.get('profile', {})
            
            result = "👤 **User Information**\n\n"
            result += f"• **Name:** {user_data.get('name', 'N/A')}\n"
            result += f"• **Real Name:** {profile.get('real_name', 'N/A')}\n"
            result += f"• **Display Name:** {profile.get('display_name', 'N/A')}\n"
            result += f"• **Title:** {profile.get('title', 'N/A')}\n"
            result += f"• **Email:** {profile.get('email', 'N/A')}\n"
            result += f"• **Phone:** {profile.get('phone', 'N/A')}\n"
            result += f"• **Status Text:** {profile.get('status_text', 'N/A')}\n"
            result += f"• **Status Emoji:** {profile.get('status_emoji', 'N/A')}\n"
            result += f"• **Timezone:** {user_data.get('tz', 'N/A')} ({user_data.get('tz_label', 'N/A')})\n"
            result += f"• **Is Bot:** {'Yes' if user_data.get('is_bot', False) else 'No'}\n"
            result += f"• **Is Admin:** {'Yes' if user_data.get('is_admin', False) else 'No'}\n"
            result += f"• **Is Owner:** {'Yes' if user_data.get('is_owner', False) else 'No'}\n"
            
            if profile.get('image_48'):
                result += f"\n• **Avatar:** {profile.get('image_48')}\n"
            
            return result
        else:
            return "❌ Failed to get user info: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("list_workspace_members")
async def list_workspace_members(limit: int = 100) -> str:
    """
    List all members in the Slack workspace.
    
    Args:
        limit: Maximum number of users to return (default: 100)
    
    Returns:
        Formatted list of workspace members
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # List users with rate limiting
        response = await make_slack_request(
            async_client.users_list,
            limit=limit
        )
        
        if response:
            members = response.get('members', [])
            active_members = [m for m in members if not m.get('deleted', False)]
            
            result = f"👥 **Workspace Members** ({len(active_members)} active, {len(members)} total)\n\n"
            
            # Group by type
            regular_users = []
            bots = []
            admins = []
            
            for member in active_members:
                if member.get('is_bot', False):
                    bots.append(member)
                elif member.get('is_admin', False) or member.get('is_owner', False):
                    admins.append(member)
                else:
                    regular_users.append(member)
            
            # Display admins
            if admins:
                result += f"**Admins & Owners ({len(admins)}):**\n"
                for i, admin in enumerate(admins[:10], 1):
                    name = admin.get('real_name', admin.get('name', 'Unknown'))
                    result += f"{i}. {name} (@{admin.get('name')})"  
                    if admin.get('is_owner'):
                        result += " 👑"
                    result += "\n"
                if len(admins) > 10:
                    result += f"... and {len(admins) - 10} more\n"
                result += "\n"
            
            # Display regular users
            if regular_users:
                result += f"**Regular Users ({len(regular_users)}):**\n"
                for i, user in enumerate(regular_users[:15], 1):
                    name = user.get('real_name', user.get('name', 'Unknown'))
                    result += f"{i}. {name} (@{user.get('name')})\n"
                if len(regular_users) > 15:
                    result += f"... and {len(regular_users) - 15} more\n"
                result += "\n"
            
            # Display bots
            if bots:
                result += f"**Bots ({len(bots)}):**\n"
                for i, bot in enumerate(bots[:5], 1):
                    name = bot.get('real_name', bot.get('name', 'Unknown'))
                    result += f"{i}. {name} 🤖\n"
                if len(bots) > 5:
                    result += f"... and {len(bots) - 5} more\n"
            
            return result
        else:
            return "❌ Failed to list workspace members: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("search_slack_users")
async def search_slack_users(query: str) -> str:
    """
    Search for users in the workspace by name or email.
    
    Args:
        query: Search query (name, display name, or email)
    
    Returns:
        List of matching users
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Get all users (Slack doesn't have a search endpoint for users)
        response = await make_slack_request(
            async_client.users_list,
            limit=1000  # Get more users for searching
        )
        
        if response:
            members = response.get('members', [])
            query_lower = query.lower()
            
            # Search through users
            matches = []
            for member in members:
                if member.get('deleted', False):  # Skip deleted users
                    continue
                    
                profile = member.get('profile', {})
                
                # Check various fields for matches
                if (query_lower in member.get('name', '').lower() or
                    query_lower in member.get('real_name', '').lower() or
                    query_lower in profile.get('display_name', '').lower() or
                    query_lower in profile.get('email', '').lower() or
                    query_lower in profile.get('title', '').lower()):
                    matches.append(member)
            
            if matches:
                result = f"🔍 **Search Results for '{query}'** ({len(matches)} found)\n\n"
                
                for i, user in enumerate(matches[:20], 1):  # Show first 20
                    profile = user.get('profile', {})
                    result += f"**{i}. {user.get('real_name', user.get('name', 'Unknown'))}**\n"
                    result += f"   • Username: @{user.get('name')}\n"
                    if profile.get('title'):
                        result += f"   • Title: {profile['title']}\n"
                    if profile.get('email'):
                        result += f"   • Email: {profile['email']}\n"
                    if user.get('is_bot'):
                        result += "   • Type: Bot 🤖\n"
                    elif user.get('is_admin') or user.get('is_owner'):
                        result += "   • Type: Admin " + ("👑" if user.get('is_owner') else "") + "\n"
                    result += "\n"
                
                if len(matches) > 20:
                    result += f"... and {len(matches) - 20} more matches\n"
            else:
                result = f"❌ No users found matching '{query}'"
            
            return result
        else:
            return "❌ Failed to search users: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("get_user_presence")
async def get_user_presence(user: str) -> str:
    """
    Get a user's current presence status.
    
    Args:
        user: User ID to check presence for
    
    Returns:
        User's presence information
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Get presence with rate limiting
        response = await make_slack_request(
            async_client.users_getPresence,
            user=user
        )
        
        if response:
            presence = response.get('presence', 'unknown')
            
            # Get user info for name
            user_info_response = await make_slack_request(
                async_client.users_info,
                user=user
            )
            
            user_name = "Unknown User"
            if user_info_response:
                user_data = user_info_response.get('user', {})
                user_name = user_data.get('real_name', user_data.get('name', 'Unknown'))
            
            result = f"🟢 **User Presence for {user_name}**\n\n"
            
            # Presence status with emoji
            if presence == 'active':
                result += "• **Status:** 🟢 Active\n"
            elif presence == 'away':
                result += "• **Status:** 🟡 Away\n"
            else:
                result += f"• **Status:** ⚪ {presence.title()}\n"
            
            # Auto-away status
            if response.get('auto_away', False):
                result += "• **Auto-away:** Yes\n"
            if response.get('manual_away', False):
                result += "• **Manual away:** Yes\n"
            
            # Last activity
            if response.get('last_activity'):
                timestamp = response['last_activity']
                last_active = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                result += f"• **Last Activity:** {last_active}\n"
            
            # Connection count
            if response.get('connection_count') is not None:
                result += f"• **Active Connections:** {response['connection_count']}\n"
            
            return result
        else:
            return "❌ Failed to get user presence: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("get_user_timezone")
async def get_user_timezone(user: str) -> str:
    """
    Get a user's timezone information.
    
    Args:
        user: User ID to get timezone for
    
    Returns:
        User's timezone details
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Get user info with rate limiting
        response = await make_slack_request(
            async_client.users_info,
            user=user
        )
        
        if response:
            user_data = response.get('user', {})
            
            result = f"🌍 **Timezone Information for {user_data.get('real_name', user_data.get('name', 'Unknown'))}**\n\n"
            result += f"• **Timezone:** {user_data.get('tz', 'Not set')}\n"
            result += f"• **Timezone Label:** {user_data.get('tz_label', 'Not set')}\n"
            result += f"• **UTC Offset:** {user_data.get('tz_offset', 0) / 3600:.1f} hours\n"
            
            # Calculate current time in user's timezone
            if user_data.get('tz_offset') is not None:
                import datetime
                utc_now = datetime.datetime.utcnow()
                user_time = utc_now + datetime.timedelta(seconds=user_data['tz_offset'])
                result += f"• **Current Time:** {user_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            return result
        else:
            return "❌ Failed to get user timezone: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("get_user_conversations")
async def get_user_conversations(types: str = "public_channel,private_channel,mpim,im", limit: int = 100) -> str:
    """
    Get all conversations (channels, DMs, etc.) the user is a member of.
    
    Args:
        types: Comma-separated list of conversation types to include
        limit: Maximum number of conversations to return (default: 100)
    
    Returns:
        List of user's conversations
    """
    try:
        validate_slack_token()
        
        # Initialize async client
        async_client = await init_async_client()
        if not async_client:
            return "❌ Failed to initialize async Slack client"
        
        # Get conversations with rate limiting
        response = await make_slack_request(
            async_client.users_conversations,
            types=types,
            limit=limit
        )
        
        if response:
            conversations = response.get('channels', [])
            
            # Group conversations by type
            public_channels = []
            private_channels = []
            direct_messages = []
            multi_person_dms = []
            
            for conv in conversations:
                if conv.get('is_channel'):
                    if conv.get('is_private'):
                        private_channels.append(conv)
                    else:
                        public_channels.append(conv)
                elif conv.get('is_im'):
                    direct_messages.append(conv)
                elif conv.get('is_mpim'):
                    multi_person_dms.append(conv)
            
            result = f"💬 **User Conversations** ({len(conversations)} total)\n\n"
            
            # Display public channels
            if public_channels:
                result += f"**Public Channels ({len(public_channels)}):**\n"
                for i, ch in enumerate(public_channels[:10], 1):
                    result += f"{i}. #{ch.get('name')} "
                    if ch.get('num_members'):
                        result += f"({ch['num_members']} members)"
                    result += "\n"
                if len(public_channels) > 10:
                    result += f"... and {len(public_channels) - 10} more\n"
                result += "\n"
            
            # Display private channels
            if private_channels:
                result += f"**Private Channels ({len(private_channels)}):**\n"
                for i, ch in enumerate(private_channels[:10], 1):
                    result += f"{i}. 🔒 #{ch.get('name')} "
                    if ch.get('num_members'):
                        result += f"({ch['num_members']} members)"
                    result += "\n"
                if len(private_channels) > 10:
                    result += f"... and {len(private_channels) - 10} more\n"
                result += "\n"
            
            # Display DMs
            if direct_messages:
                result += f"**Direct Messages ({len(direct_messages)}):**\n"
                for i, dm in enumerate(direct_messages[:10], 1):
                    result += f"{i}. DM with <@{dm.get('user')}>\n"
                if len(direct_messages) > 10:
                    result += f"... and {len(direct_messages) - 10} more\n"
                result += "\n"
            
            # Display multi-person DMs
            if multi_person_dms:
                result += f"**Group DMs ({len(multi_person_dms)}):**\n"
                for i, mpim in enumerate(multi_person_dms[:5], 1):
                    result += f"{i}. {mpim.get('name', 'Group DM')}\n"
                if len(multi_person_dms) > 5:
                    result += f"... and {len(multi_person_dms) - 5} more\n"
            
            return result
        else:
            return "❌ Failed to get user conversations: API request failed"
            
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
