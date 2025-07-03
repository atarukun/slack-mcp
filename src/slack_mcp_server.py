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
