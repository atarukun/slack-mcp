"""Unit tests for message management tools."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from slack_sdk.errors import SlackApiError

from slack_mcp.tools import message_management


class TestMessageManagementTools:
    """Test cases for message management Slack MCP tools."""
    
    def test_register_tools(self, mock_mcp_server):
        """Test that all message management tools are properly registered."""
        message_management.register_tools(mock_mcp_server)
        
        # Verify tool decorator was called for each tool
        assert mock_mcp_server.tool.call_count >= 8  # At least 8 message management tools
        
        # Check that specific tools were registered
        tool_names = [call[0][0] for call in mock_mcp_server.tool.call_args_list]
        expected_tools = [
            "update_message",
            "delete_message",
            "pin_message",
            "unpin_message",
            "get_message_permalink",
            "schedule_message",
            "get_thread_replies",
            "send_direct_message"
        ]
        for tool in expected_tools:
            assert tool in tool_names
    
    @pytest.mark.asyncio
    @patch('slack_mcp.tools.message_management.init_async_client')
    @patch('slack_mcp.tools.message_management.make_slack_request')
    @patch('slack_mcp.tools.message_management.validate_slack_token')
    async def test_update_message_success(self, mock_validate, mock_make_request, mock_init_client, mock_mcp_server):
        """Test updating a message successfully."""
        # Setup mocks
        mock_validate.return_value = None
        mock_async_client = AsyncMock()
        mock_init_client.return_value = mock_async_client
        
        mock_make_request.return_value = {
            "ok": True,
            "channel": "C123",
            "ts": "1234567890.123456",
            "text": "Updated message"
        }
        
        # Register tools and get the function
        message_management.register_tools(mock_mcp_server)
        update_msg_func = None
        for call in mock_mcp_server.tool.call_args_list:
            if call[0][0] == "update_message":
                update_msg_func = call[0][1]
                break
        
        # Test updating message
        result = await update_msg_func(
            channel="C123",
            ts="1234567890.123456",
            text="Updated message"
        )
        
        assert "✅ **Message Updated Successfully**" in result
        assert "Channel: C123" in result
        assert "Updated message" in result
    
    @pytest.mark.asyncio
    @patch('slack_mcp.tools.message_management.init_async_client')
    @patch('slack_mcp.tools.message_management.make_slack_request')
    @patch('slack_mcp.tools.message_management.validate_slack_token')
    async def test_delete_message_success(self, mock_validate, mock_make_request, mock_init_client, mock_mcp_server):
        """Test deleting a message successfully."""
        # Setup mocks
        mock_validate.return_value = None
        mock_async_client = AsyncMock()
        mock_init_client.return_value = mock_async_client
        
        mock_make_request.return_value = {
            "ok": True,
            "channel": "C123",
            "ts": "1234567890.123456"
        }
        
        # Register tools and get the function
        message_management.register_tools(mock_mcp_server)
        delete_msg_func = None
        for call in mock_mcp_server.tool.call_args_list:
            if call[0][0] == "delete_message":
                delete_msg_func = call[0][1]
                break
        
        # Test deleting message
        result = await delete_msg_func(
            channel="C123",
            ts="1234567890.123456"
        )
        
        assert "✅ **Message Deleted Successfully**" in result
        assert "Channel: C123" in result
    
    @pytest.mark.asyncio
    @patch('slack_mcp.tools.message_management.init_async_client')
    @patch('slack_mcp.tools.message_management.make_slack_request')
    @patch('slack_mcp.tools.message_management.validate_slack_token')
    async def test_schedule_message_success(self, mock_validate, mock_make_request, mock_init_client, mock_mcp_server):
        """Test scheduling a message successfully."""
        # Setup mocks
        mock_validate.return_value = None
        mock_async_client = AsyncMock()
        mock_init_client.return_value = mock_async_client
        
        mock_make_request.return_value = {
            "ok": True,
            "scheduled_message_id": "Q1234567890",
            "channel": "C123",
            "post_at": 1735689600
        }
        
        # Register tools and get the function
        message_management.register_tools(mock_mcp_server)
        schedule_msg_func = None
        for call in mock_mcp_server.tool.call_args_list:
            if call[0][0] == "schedule_message":
                schedule_msg_func = call[0][1]
                break
        
        # Test scheduling message
        result = await schedule_msg_func(
            channel="C123",
            text="Future message",
            post_at=1735689600
        )
        
        assert "✅ **Message Scheduled Successfully**" in result
        assert "Scheduled ID: Q1234567890" in result
        assert "Channel: C123" in result
