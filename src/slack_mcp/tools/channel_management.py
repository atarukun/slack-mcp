"""
Channel management tools for Slack MCP Server.
Includes channel creation, configuration, and membership management.
"""
from typing import Optional
from datetime import datetime
from slack_sdk.errors import SlackApiError

from ..utils.client import (
    validate_slack_token,
    init_async_client,
)
from ..utils.errors import make_slack_request
from ..models.schemas import ChannelInfo


def register_tools(mcp):
    """Register all channel management tools with the provided MCP instance."""
    
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
