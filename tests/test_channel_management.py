"""Unit tests for channel management tools."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from slack_sdk.errors import SlackApiError

from slack_mcp.tools import channel_management


class TestChannelManagementTools:
    """Test cases for channel management Slack MCP tools."""
    
    def test_register_tools(self, mock_mcp_server):
        """Test that all channel management tools are properly registered."""
        channel_management.register_tools(mock_mcp_server)
        
        # Verify tool decorator was called for each tool
        assert mock_mcp_server.tool.call_count >= 9  # At least 9 channel management tools
        
        # Check that specific tools were registered
        tool_names = [call[0][0] for call in mock_mcp_server.tool.call_args_list]
        expected_tools = [
            "create_channel",
            "archive_channel",
            "join_channel",
            "leave_channel",
            "invite_to_channel",
            "remove_from_channel",
            "set_channel_topic",
            "set_channel_purpose",
            "list_channel_members"
        ]
        for tool in expected_tools:
            assert tool in tool_names
    
    @pytest.mark.asyncio
    @patch('slack_mcp.tools.channel_management.init_async_client')
    @patch('slack_mcp.tools.channel_management.make_slack_request')
    @patch('slack_mcp.tools.channel_management.validate_slack_token')
    async def test_create_channel_success(self, mock_validate, mock_make_request, mock_init_client, mock_mcp_server):
        """Test creating a channel successfully."""
        # Setup mocks
        mock_validate.return_value = None
        mock_async_client = AsyncMock()
        mock_init_client.return_value = mock_async_client
        
        mock_make_request.return_value = {
            "ok": True,
            "channel": {
                "id": "C123NEW",
                "name": "new-channel",
                "is_channel": True,
                "is_private": False,
                "created": 1234567890
            }
        }
        
        # Register tools and get the function
        channel_management.register_tools(mock_mcp_server)
        create_channel_func = None
        for call in mock_mcp_server.tool.call_args_list:
            if call[0][0] == "create_channel":
                create_channel_func = call[0][1]
                break
        
        # Test creating channel
        result = await create_channel_func(
            name="new-channel",
            is_private=False
        )
        
        assert "✅ **Channel Created Successfully**" in result
        assert "Name: #new-channel" in result
        assert "ID: C123NEW" in result
    
    @pytest.mark.asyncio
    @patch('slack_mcp.tools.channel_management.init_async_client')
    @patch('slack_mcp.tools.channel_management.make_slack_request')
    @patch('slack_mcp.tools.channel_management.validate_slack_token')
    async def test_archive_channel_success(self, mock_validate, mock_make_request, mock_init_client, mock_mcp_server):
        """Test archiving a channel successfully."""
        # Setup mocks
        mock_validate.return_value = None
        mock_async_client = AsyncMock()
        mock_init_client.return_value = mock_async_client
        
        mock_make_request.return_value = {
            "ok": True
        }
        
        # Register tools and get the function
        channel_management.register_tools(mock_mcp_server)
        archive_channel_func = None
        for call in mock_mcp_server.tool.call_args_list:
            if call[0][0] == "archive_channel":
                archive_channel_func = call[0][1]
                break
        
        # Test archiving channel
        result = await archive_channel_func(channel="C123")
        
        assert "✅ **Channel Archived Successfully**" in result
        assert "Channel C123" in result
    
    @pytest.mark.asyncio
    @patch('slack_mcp.tools.channel_management.init_async_client')
    @patch('slack_mcp.tools.channel_management.make_slack_request')
    @patch('slack_mcp.tools.channel_management.validate_slack_token')
    async def test_invite_to_channel_success(self, mock_validate, mock_make_request, mock_init_client, mock_mcp_server):
        """Test inviting users to a channel successfully."""
        # Setup mocks
        mock_validate.return_value = None
        mock_async_client = AsyncMock()
        mock_init_client.return_value = mock_async_client
        
        mock_make_request.return_value = {
            "ok": True,
            "channel": {
                "id": "C123",
                "name": "general"
            }
        }
        
        # Register tools and get the function
        channel_management.register_tools(mock_mcp_server)
        invite_func = None
        for call in mock_mcp_server.tool.call_args_list:
            if call[0][0] == "invite_to_channel":
                invite_func = call[0][1]
                break
        
        # Test inviting users
        result = await invite_func(
            channel="C123",
            users="U123,U456"
        )
        
        assert "✅ **Users Invited Successfully**" in result
        assert "Users: U123,U456" in result
        assert "Channel: general (C123)" in result
