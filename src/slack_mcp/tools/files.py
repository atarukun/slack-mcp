"""
File operations tools for Slack MCP Server.
Includes file upload, download, listing, and management functionality.
"""

import os
import logging
from typing import Optional
from datetime import datetime
from slack_sdk.errors import SlackApiError
import aiohttp

from ..utils.client import (
    MCP_USER_AGENT,
    validate_slack_token,
    init_async_client,
)
from ..utils.errors import (
    make_slack_request,
)
from ..utils.formatting import (
    format_file_info,
)

# Configure logging
logger = logging.getLogger(__name__)


def register_tools(mcp):
    """Register all file operation tools with the provided MCP instance."""
    
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
            
            # Log the upload parameters for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Attempting file upload with params: channels={channels}, filename={filename or 'file.txt'}, title={title}, content_length={len(content) if content else 0}")
            
            # Use files_upload_v2 which is the working method
            try:
                response = await make_slack_request(
                    async_client.files_upload_v2,
                    channels=channels,
                    content=content,
                    filename=filename or "file.txt",
                    title=title,
                    initial_comment=initial_comment
                )
                logger.info(f"Upload response: {response}")
            except Exception as upload_error:
                logger.error(f"Upload error: {type(upload_error).__name__}: {str(upload_error)}")
                raise
            
            if response:
                file_info = response.get('file', {})
                
                result = "✅ **File Uploaded Successfully**\n\n"
                result += f"• **File ID:** {file_info.get('id', 'N/A')}\n"
                result += f"• **Name:** {file_info.get('name', filename or 'file.txt')}\n"
                if file_info.get('title'):
                    result += f"• **Title:** {file_info['title']}\n"
                
                # File size
                if file_info.get('size'):
                    size = file_info['size']
                    if size < 1024:
                        size_str = f"{size} bytes"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f} KB"
                    else:
                        size_str = f"{size / (1024 * 1024):.1f} MB"
                    result += f"• **Size:** {size_str}\n"
                
                result += f"\n• **Shared to:** {channels}\n"
                if initial_comment:
                    result += f"• **Comment:** {initial_comment}\n"
                
                # Add permalink if available
                if file_info.get('permalink'):
                    result += f"\n• **Permalink:** {file_info['permalink']}\n"
                    
                return result
            else:
                logger.error("Upload failed: No response received from Slack API")
                return "❌ Failed to upload file: No response received from Slack API"
                
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
            
            # Also check file extension if type is not available
            text_extensions = ['.txt', '.text', '.js', '.py', '.java', '.c', '.cpp', '.cs', '.go', '.rs',
                             '.rb', '.php', '.swift', '.kt', '.scala', '.r', '.sql', '.sh', '.yaml', '.yml',
                             '.json', '.xml', '.html', '.css', '.md', '.csv', '.log', '.conf', '.ini']
            
            file_extension = os.path.splitext(file_name.lower())[1]
            
            is_text_file = (
                file_type.lower() in text_types or 
                mimetype.startswith('text/') or 
                mimetype == 'application/json' or
                mimetype == 'application/xml' or
                mimetype == 'application/javascript' or
                file_extension in text_extensions  # Check file extension as fallback
            )
            
            if not is_text_file:
                return f"❌ Cannot display content: File '{file_name}' is not a text file (type: {file_type or mimetype or 'unknown'})"
            
            # Get download URL
            download_url = file_info.get('url_private_download')
            if not download_url:
                return "❌ No download URL available for this file"
            
            # Download the file content using aiohttp
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
