"""
Core tools for Slack MCP Server.
Includes authentication, basic messaging, and core functionality tools.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from ..utils.client import (
    MCP_USER_AGENT,
    validate_slack_token,
    init_async_client,
    set_slack_client,  # For the set_slack_token tool
)
from ..utils.errors import (
    MIN_API_INTERVAL,
    make_slack_request,
)
from ..models.schemas import (
    ChannelInfo,
    MessageInfo,
    UserInfo,
    FileUploadInfo,
)

# Import mcp from the main server module
try:
    import sys
    from pathlib import Path
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from slack_mcp_server import mcp
except ImportError:
    # Try alternative import
    from ...slack_mcp_server import mcp


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
    try:
        # Validate token format
        if not token.startswith(('xoxb-', 'xoxp-', 'xoxo-', 'xapp-')):
            return {
                "success": False,
                "error": "Invalid token format. Token should start with 'xoxb-', 'xoxp-', 'xoxo-', or 'xapp-'"
            }
        
        # Initialize client and test connection
        test_client = WebClient(token=token, user_agent_prefix=MCP_USER_AGENT)
        auth_response = test_client.auth_test()
        
        if auth_response["ok"]:
            set_slack_client(test_client)
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

