"""
Formatting utilities for Slack MCP Server.
Provides helpers for formatting messages, files, and other data.
"""
from typing import Dict, Any
from datetime import datetime


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
