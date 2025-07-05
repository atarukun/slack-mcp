"""
Message management tools for Slack MCP Server.
Includes extended messaging functionality like editing, deleting, pinning, and scheduling.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from slack_sdk.errors import SlackApiError

from ..utils.client import (
    validate_slack_token,
    init_async_client,
)
from ..utils.errors import make_slack_request
from ..models.schemas import MessageInfo


def register_tools(mcp):
    """Register all message management tools with the provided MCP instance."""
    
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
            
            # Import rate_limit_check from errors module
            from ..utils.errors import rate_limit_check
            
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
