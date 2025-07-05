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


def register_tools(mcp):
    """Register all core tools with the provided MCP instance."""
    
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

    @mcp.tool("list_channels")
    async def list_channels(
        include_archived: bool = False,
        types: str = "public_channel,private_channel"
    ) -> str:
        """
        List all channels in the Slack workspace.
        
        Args:
            include_archived: Whether to include archived channels (default: False)
            types: Comma-separated list of channel types to include (default: public and private channels)
        
        Returns:
            Formatted list of channels with details
        """
        try:
            validate_slack_token()
            
            # Initialize async client
            async_client = await init_async_client()
            if not async_client:
                return "❌ Failed to initialize async Slack client"
            
            # Get all channels with rate limiting
            channels = []
            cursor = None
            
            while True:
                params = {
                    "types": types,
                    "exclude_archived": not include_archived,
                    "limit": 200,
                }
                if cursor:
                    params["cursor"] = cursor
                
                response = await make_slack_request(
                    async_client.conversations_list,
                    **params
                )
                
                if not response:
                    break
                
                channels.extend(response.get('channels', []))
                
                # Check for pagination
                next_cursor = response.get('response_metadata', {}).get('next_cursor')
                if not next_cursor:
                    break
                cursor = next_cursor
            
            if not channels:
                return "No channels found."
            
            # Sort channels by type and name
            public_channels = sorted(
                [ch for ch in channels if not ch.get('is_private', False) and not ch.get('is_archived', False)], 
                key=lambda x: x.get('name', '')
            )
            private_channels = sorted(
                [ch for ch in channels if ch.get('is_private', False) and not ch.get('is_archived', False)], 
                key=lambda x: x.get('name', '')
            )
            archived_channels = sorted(
                [ch for ch in channels if ch.get('is_archived', False)], 
                key=lambda x: x.get('name', '')
            )
            
            result = f"📋 **Slack Channels** ({len(channels)} total)\n\n"
            
            # Format public channels
            if public_channels:
                result += "**🔓 Public Channels:**\n"
                for ch in public_channels[:10]:  # Limit display
                    name = ch.get('name', 'N/A')
                    members = ch.get('num_members', 0)
                    topic = ch.get('topic', {}).get('value', '')
                    result += f"• **#{name}** ({members} members)\n"
                    if topic and topic != "No topic":
                        result += f"  📝 {topic[:50]}{'...' if len(topic) > 50 else ''}\n"
                result += "\n"
            
            # Format private channels
            if private_channels:
                result += "**🔒 Private Channels:**\n"
                for ch in private_channels[:5]:  # Limit display
                    name = ch.get('name', 'N/A')
                    members = ch.get('num_members', 0)
                    result += f"• **{name}** ({members} members)\n"
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
            
        except ValueError as e:
            return f"❌ Configuration Error: {str(e)}"
        except SlackApiError as e:
            return f"❌ Slack API Error: {e.response['error']}"
        except Exception as e:
            return f"❌ Unexpected Error: {str(e)}"

    @mcp.tool("get_channel_info")
    async def get_channel_info(channel: str) -> str:
        """
        Get detailed information about a specific channel.
        
        Args:
            channel: Channel ID or name (e.g., 'C1234567890' or '#general')
        
        Returns:
            Detailed channel information including members, topic, purpose, etc.
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
                ch = response.get('channel', {})
                
                result = f"📢 **Channel Information**\n\n"
                result += f"• **Name:** {'#' if not ch.get('is_private') else ''}{ch.get('name', 'N/A')}\n"
                result += f"• **ID:** {ch.get('id', 'N/A')}\n"
                result += f"• **Type:** {'Private' if ch.get('is_private') else 'Public'} Channel\n"
                result += f"• **Archived:** {'Yes' if ch.get('is_archived') else 'No'}\n"
                
                if ch.get('topic', {}).get('value'):
                    result += f"• **Topic:** {ch['topic']['value']}\n"
                
                if ch.get('purpose', {}).get('value'):
                    result += f"• **Purpose:** {ch['purpose']['value']}\n"
                
                result += f"• **Members:** {ch.get('num_members', 0)}\n"
                
                if ch.get('created'):
                    created_time = datetime.fromtimestamp(ch['created']).strftime('%Y-%m-%d %H:%M:%S')
                    result += f"• **Created:** {created_time}\n"
                
                if ch.get('creator'):
                    result += f"• **Created by:** <@{ch['creator']}>\n"
                
                # Get member list for smaller channels
                if ch.get('num_members', 0) <= 100:
                    members_response = await make_slack_request(
                        async_client.conversations_members,
                        channel=channel,
                        limit=100
                    )
                    if members_response and members_response.get('members'):
                        result += f"\n**Members ({len(members_response['members'])}):**\n"
                        member_list = [f"<@{m}>" for m in members_response['members'][:20]]
                        result += ", ".join(member_list)
                        if len(members_response['members']) > 20:
                            result += f"\n... and {len(members_response['members']) - 20} more"
                
                return result
            else:
                return "❌ Failed to get channel info: API request failed"
                
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
            
            # Determine if input is email or user ID
            response = None
            if '@' in user:
                # Try looking up by email
                try:
                    response = await make_slack_request(
                        async_client.users_lookupByEmail,
                        email=user
                    )
                except SlackApiError as e:
                    if e.response['error'] == 'users_not_found':
                        return f"❌ User not found with email: {user}"
                    raise
            else:
                # Try direct user ID lookup
                try:
                    response = await make_slack_request(
                        async_client.users_info,
                        user=user
                    )
                except SlackApiError as e:
                    if e.response['error'] == 'user_not_found':
                        return f"❌ User not found with ID: {user}"
                    raise
            
            if response:
                user_data = response.get('user', {})
                profile = user_data.get('profile', {})
                
                result = "👤 **User Information**\n\n"
                result += f"• **User ID:** {user_data.get('id', 'N/A')}\n"
                result += f"• **Username:** {user_data.get('name', 'N/A')}\n"
                result += f"• **Real Name:** {profile.get('real_name', 'N/A')}\n"
                result += f"• **Display Name:** {profile.get('display_name', 'N/A')}\n"
                
                if profile.get('title'):
                    result += f"• **Title:** {profile['title']}\n"
                
                if profile.get('email'):
                    result += f"• **Email:** {profile['email']}\n"
                
                if profile.get('phone'):
                    result += f"• **Phone:** {profile['phone']}\n"
                
                # Status
                if profile.get('status_text') or profile.get('status_emoji'):
                    result += f"\n**Status:**\n"
                    if profile.get('status_emoji'):
                        result += f"• Emoji: {profile['status_emoji']}\n"
                    if profile.get('status_text'):
                        result += f"• Text: {profile['status_text']}\n"
                
                # Timezone
                if user_data.get('tz'):
                    result += f"\n**Timezone:** {user_data['tz']} ({user_data.get('tz_label', 'N/A')})\n"
                
                # Account type
                result += f"\n**Account Type:**\n"
                result += f"• Is Bot: {'Yes' if user_data.get('is_bot', False) else 'No'}\n"
                result += f"• Is Admin: {'Yes' if user_data.get('is_admin', False) else 'No'}\n"
                result += f"• Is Owner: {'Yes' if user_data.get('is_owner', False) else 'No'}\n"
                result += f"• Is Guest: {'Yes' if user_data.get('is_restricted', False) or user_data.get('is_ultra_restricted', False) else 'No'}\n"
                
                if profile.get('image_192'):
                    result += f"\n**Avatar URL:** {profile['image_192']}\n"
                
                return result
            else:
                return "❌ Failed to get user info: API request failed"
                
        except ValueError as e:
            return f"❌ Configuration Error: {str(e)}"
        except SlackApiError as e:
            error_msg = e.response['error']
            if error_msg == 'missing_scope':
                return f"❌ Missing required scope. Ensure your token has 'users:read' and 'users:read.email' scopes."
            elif error_msg == 'user_not_visible':
                return f"❌ User is not visible. This may be a guest user or from another workspace."
            else:
                return f"❌ Slack API Error: {error_msg}"
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

