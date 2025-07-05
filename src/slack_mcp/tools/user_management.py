"""
User management tools for Slack MCP Server.
Includes workspace member listing, user search, and user information retrieval.
"""
from typing import Optional
from datetime import datetime
from slack_sdk.errors import SlackApiError

from ..utils.client import (
    validate_slack_token,
    init_async_client,
)
from ..utils.errors import make_slack_request
from ..models.schemas import UserInfo


def register_tools(mcp):
    """Register all user management tools with the provided MCP instance."""
    
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
