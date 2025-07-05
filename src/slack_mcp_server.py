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
import time
import json
from datetime import datetime

# Import utilities and models from the new package structure
try:
    # Try absolute import first (when installed as package)
    from slack_mcp.utils import (
        # Client utilities
        MCP_USER_AGENT,
        validate_slack_token,
        init_async_client,
        get_slack_client,
        set_slack_client,
        get_async_slack_client,
        # Formatting utilities
        format_file_info,
        # Error handling utilities
        MIN_API_INTERVAL,
        rate_limit_check,
        make_slack_request,
    )
    from slack_mcp.models import (
        SlackTokenValidation,
        ChannelInfo,
        MessageInfo,
        UserInfo,
        FileUploadInfo,
    )
except ImportError:
    # Fall back to relative import (when running directly)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from slack_mcp.utils import (
        # Client utilities
        MCP_USER_AGENT,
        validate_slack_token,
        init_async_client,
        get_slack_client,
        set_slack_client,
        get_async_slack_client,
        # Formatting utilities
        format_file_info,
        # Error handling utilities
        MIN_API_INTERVAL,
        rate_limit_check,
        make_slack_request,
    )
    from slack_mcp.models import (
        SlackTokenValidation,
        ChannelInfo,
        MessageInfo,
        UserInfo,
        FileUploadInfo,
    )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("slack", description="A comprehensive MCP server for Slack API operations")

# Import and register tools
try:
    from slack_mcp.tools import core as tools_core
    from slack_mcp.tools import message_management as tools_message_mgmt
    from slack_mcp.tools import channel_management as tools_channel_mgmt
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from slack_mcp.tools import core as tools_core
    from slack_mcp.tools import message_management as tools_message_mgmt
    from slack_mcp.tools import channel_management as tools_channel_mgmt

# Register tools from the tools modules
tools_core.register_tools(mcp)
tools_message_mgmt.register_tools(mcp)
tools_channel_mgmt.register_tools(mcp)

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
        
        # Build parameters
        params = {
            "count": min(count, 100),  # Max 100 per Slack API
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
            paging = response.get('paging', {})
            
            if not files:
                return "📁 No files found matching the criteria"
            
            result = f"📁 **Files List** (Page {paging.get('page', 1)} of {paging.get('pages', 1)})\n\n"
            
            for file in files:
                result += f"**{file.get('name', 'Unnamed')}**\n"
                result += f"• **ID:** {file.get('id', 'N/A')}\n"
                result += f"• **Type:** {file.get('filetype', 'Unknown').upper()}\n"
                
                # Size formatting
                if file.get('size'):
                    size = file['size']
                    if size < 1024:
                        size_str = f"{size} bytes"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f} KB"
                    else:
                        size_str = f"{size / (1024 * 1024):.1f} MB"
                    result += f"• **Size:** {size_str}\n"
                
                # Upload info
                if file.get('user'):
                    result += f"• **Uploaded by:** <@{file['user']}>\n"
                
                if file.get('created'):
                    upload_time = datetime.fromtimestamp(file['created']).strftime('%Y-%m-%d %H:%M:%S')
                    result += f"• **Uploaded:** {upload_time}\n"
                
                # Sharing info
                shared_in = []
                if file.get('channels'):
                    shared_in.extend([f"<#{ch}>" for ch in file['channels']])
                if file.get('groups'):
                    shared_in.append(f"{len(file['groups'])} private channel(s)")
                if file.get('ims'):
                    shared_in.append(f"{len(file['ims'])} DM(s)")
                
                if shared_in:
                    result += f"• **Shared in:** {', '.join(shared_in)}\n"
                
                result += "\n"
            
            # Pagination info
            result += f"**Total files:** {paging.get('total', 0)}\n"
            if paging.get('pages', 1) > 1:
                result += f"Use `page` parameter to navigate (1-{paging['pages']})\n"
            
            return result
        else:
            return "❌ Failed to list files: API request failed"
            
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

@mcp.tool("get_file_content")
async def get_file_content(
    file_id: str,
    max_size_mb: float = 10
) -> str:
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
        
        # First get file info to check size and type
        info_response = await make_slack_request(
            async_client.files_info,
            file=file_id
        )
        
        if not info_response:
            return "❌ File not found or inaccessible"
        
        file_info = info_response.get('file', {})
        file_name = file_info.get('name', 'Unknown')
        file_size = file_info.get('size', 0)
        file_type = file_info.get('filetype', '')
        mimetype = file_info.get('mimetype', '')
        
        # Check file size
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            return f"❌ File too large: {file_size / (1024 * 1024):.1f}MB (max: {max_size_mb}MB)"
        
        # Check if it's a text-based file
        text_types = ['text', 'javascript', 'python', 'java', 'c', 'cpp', 'csharp', 'go', 'rust', 
                      'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'sql', 'shell', 'yaml', 
                      'json', 'xml', 'html', 'css', 'markdown', 'csv', 'log', 'conf', 'ini']
        
        is_text_file = (
            file_type.lower() in text_types or 
            mimetype.startswith('text/') or 
            mimetype == 'application/json' or
            mimetype == 'application/xml' or
            mimetype == 'application/javascript'
        )
        
        if not is_text_file:
            return f"❌ Cannot display content: File '{file_name}' is not a text file (type: {file_type or mimetype})"
        
        # Get download URL
        download_url = file_info.get('url_private_download')
        if not download_url:
            return "❌ No download URL available for this file"
        
        # Download the file content using aiohttp
        import aiohttp
        headers = {
            "Authorization": f"Bearer {os.getenv('SLACK_BOT_TOKEN')}",
            "User-Agent": MCP_USER_AGENT
        }
        
        # Configure timeout settings
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(download_url, headers=headers) as response:
                    response.raise_for_status()
                    content = await response.text()
                
                # Format the response
                result = f"📄 **File Content**\n\n"
                result += f"**File:** {file_name}\n"
                result += f"**Type:** {file_type.upper() if file_type else 'Text'}\n"
                result += f"**Size:** {len(content)} characters\n\n"
                result += "```\n"
                
                # Truncate very long files
                if len(content) > 50000:
                    result += content[:50000]
                    result += "\n\n... (content truncated)\n"
                else:
                    result += content
                
                result += "\n```"
                
                return result
                
            except aiohttp.ClientConnectorError as e:
                logger.error(f"ClientConnectorError in get_file_content: {str(e)}")
                return f"❌ Connection error: Unable to connect to Slack file server. {str(e)}"
            except aiohttp.ServerTimeoutError as e:
                logger.error(f"ServerTimeoutError in get_file_content: {str(e)}")
                return f"❌ Server timeout: The file download took too long. Try again with a smaller file."
            except aiohttp.ClientResponseError as e:
                logger.error(f"ClientResponseError in get_file_content: {e.status} - {e.message}")
                return f"❌ HTTP Error {e.status}: {e.message}"
            except aiohttp.ClientError as e:
                # More specific error details
                error_type = type(e).__name__
                error_msg = str(e)
                logger.error(f"ClientError in get_file_content ({error_type}): {error_msg}")
                return f"❌ Failed to download file ({error_type}): {error_msg}"
            except Exception as e:
                logger.error(f"Unexpected error in get_file_content: {type(e).__name__} - {str(e)}", exc_info=True)
                return f"❌ Unexpected download error: {type(e).__name__} - {str(e)}"
                
    except ValueError as e:
        return f"❌ Configuration Error: {str(e)}"
    except SlackApiError as e:
        return f"❌ Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

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
        file_permalink = file_info.get('permalink', '')
        
        channel_list = [ch.strip() for ch in channels.split(',')]
        shared_to = []
        failed = []
        
        # Check current shares
        current_channels = set(file_info.get('channels', []))
        current_groups = set(file_info.get('groups', []))
        
        for channel in channel_list:
            try:
                # Check if already shared
                if channel in current_channels or channel in current_groups:
                    shared_to.append(f"{channel} (already shared)")
                    continue
                
                # Send a message with the file link
                msg_params = {
                    "channel": channel,
                    "text": comment or f"Shared file: {file_name}\n{file_permalink}",
                    "unfurl_links": True,
                    "unfurl_media": True
                }
                
                # If we have blocks, use them
                if comment:
                    msg_params["blocks"] = [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": comment
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"📎 *File:* <{file_permalink}|{file_name}>"
                            }
                        }
                    ]
                
                response = await make_slack_request(
                    async_client.chat_postMessage,
                    **msg_params
                )
                
                if response:
                    shared_to.append(channel)
                else:
                    failed.append(f"{channel} (no response)")
                    
            except SlackApiError as e:
                error_msg = e.response.get('error', 'Unknown error')
                if error_msg == 'channel_not_found':
                    failed.append(f"{channel} (channel not found - check if bot is member)")
                elif error_msg == 'not_in_channel':
                    failed.append(f"{channel} (bot not in channel)")
                else:
                    failed.append(f"{channel} ({error_msg})")
                logger.error(f"Slack API error sharing to {channel}: {error_msg}")
            except Exception as e:
                logger.error(f"Failed to share to {channel}: {str(e)}")
                failed.append(f"{channel} (error: {str(e)})")
        
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

# Phase 4: Extended Messaging Tools
# Tools moved to slack_mcp.tools.message_management

# Phase 5: Channel Management Tools
# Tools moved to slack_mcp.tools.channel_management

# ========================================
# Phase 6: User Management Tools
# ========================================
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
        # Use the client utility function to set the client
        test_client = WebClient(token=slack_token, user_agent_prefix=MCP_USER_AGENT)
        set_slack_client(test_client)
        logger.info("Slack client initialized from environment variable")
    else:
        logger.info("No SLACK_BOT_TOKEN found in environment. Use set_slack_token tool to configure.")
    
    mcp.run(transport='stdio')

if __name__ == "__main__":
    run_server()
