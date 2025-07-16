"""Unit tests for core tools."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from slack_sdk.errors import SlackApiError

from slack_mcp.tools import core
from slack_mcp.utils.client import set_slack_client


class TestCoreTools:
    """Test cases for core Slack MCP tools."""
    
    def test_register_tools(self, mock_mcp_server):
        """Test that all core tools are properly registered."""
        core.register_tools(mock_mcp_server)
        
        # Verify tool decorator was called for each tool
        assert mock_mcp_server.tool.call_count >= 7  # At least 7 core tools
        
        # Check that specific tools were registered
        tool_names = [call[0][0] for call in mock_mcp_server.tool.call_args_list]
        expected_tools = [
            "set_slack_token",
            "test_slack_connection", 
            "send_message",
            "list_channels",
            "get_channel_info",
            "get_user_info"
        ]
        for tool in expected_tools:
            assert tool in tool_names
    
    @patch('slack_mcp.tools.core.WebClient')
    @patch('slack_mcp.tools.core.set_slack_client')
    def test_set_slack_token_valid(self, mock_set_client, mock_webclient_class, mock_mcp_server):
        """Test setting a valid Slack token."""
        # Setup mock
        mock_client = MagicMock()
        mock_webclient_class.return_value = mock_client
        mock_client.auth_test.return_value = {
            "ok": True,
            "bot_id": "B123",
            "user_id": "U123",
            "team": "Test Team",
            "team_id": "T123"
        }
        
        # Register tools and get the function
        core.register_tools(mock_mcp_server)
        set_token_func = None
        for call in mock_mcp_server.tool.call_args_list:
            if call[0][0] == "set_slack_token":
                set_token_func = call[0][1]
                break
        
        # Test valid token
        result = set_token_func("xoxb-valid-token")
        
        assert result["success"] is True
        assert "bot_id" in result
        assert result["bot_id"] == "B123"
        mock_set_client.assert_called_once_with(mock_client)
    
    def test_set_slack_token_invalid_format(self, mock_mcp_server):
        """Test setting an invalid token format."""
        # Register tools and get the function
        core.register_tools(mock_mcp_server)
        set_token_func = None
        for call in mock_mcp_server.tool.call_args_list:
            if call[0][0] == "set_slack_token":
                set_token_func = call[0][1]
                break
        
        # Test invalid token format
        result = set_token_func("invalid-token")
        
        assert result["success"] is False
        assert "Invalid token format" in result["error"]
    
    @pytest.mark.asyncio
    @patch('slack_mcp.tools.core.init_async_client')
    @patch('slack_mcp.tools.core.make_slack_request')
    @patch('slack_mcp.tools.core.validate_slack_token')
    async def test_test_slack_connection_success(self, mock_validate, mock_make_request, mock_init_client, mock_mcp_server):
        """Test successful Slack connection test."""
        # Setup mocks
        mock_validate.return_value = None  # No exception
        mock_async_client = AsyncMock()
        mock_init_client.return_value = mock_async_client
        
        # Mock API responses
        mock_make_request.side_effect = [
            {  # auth_test response
                "ok": True,
                "bot_id": "B123",
                "user_id": "U123", 
                "team": "Test Team",
                "team_id": "T123",
                "url": "https://test.slack.com"
            },
            {  # team_info response
                "ok": True,
                "team": {
                    "name": "Test Team",
                    "domain": "testteam",
                    "email_domain": "testteam.com",
                    "icon": {"image_132": "https://test.com/icon.png"}
                }
            }
        ]
        
        # Register tools and get the function
        core.register_tools(mock_mcp_server)
        test_conn_func = None
        for call in mock_mcp_server.tool.call_args_list:
            if call[0][0] == "test_slack_connection":
                test_conn_func = call[0][1]
                break
        
        # Test connection
        result = await test_conn_func()
        
        assert "✅ **Slack Connection Successful**" in result
        assert "Bot ID: B123" in result
        assert "Team: Test Team" in result
        assert "Workspace Information" in result
    
    @pytest.mark.asyncio
    @patch('slack_mcp.tools.core.init_async_client')
    @patch('slack_mcp.tools.core.make_slack_request') 
    @patch('slack_mcp.tools.core.validate_slack_token')
    async def test_send_message_success(self, mock_validate, mock_make_request, mock_init_client, mock_mcp_server):
        """Test sending a message successfully."""
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
        core.register_tools(mock_mcp_server)
        send_msg_func = None
        for call in mock_mcp_server.tool.call_args_list:
            if call[0][0] == "send_message":
                send_msg_func = call[0][1]
                break
        
        # Test sending message
        result = await send_msg_func(channel="#general", text="Hello, World!")
        
        assert "✅ **Message Sent Successfully**" in result
        assert "Channel: C123" in result
        assert "Hello, World!" in result
    
    @pytest.mark.asyncio
    @patch('slack_mcp.tools.core.validate_slack_token')
    async def test_send_message_no_token(self, mock_validate, mock_mcp_server):
        """Test sending a message without a token."""
        # Setup mock to raise ValueError
        mock_validate.side_effect = ValueError("No token configured")
        
        # Register tools and get the function
        core.register_tools(mock_mcp_server)
        send_msg_func = None
        for call in mock_mcp_server.tool.call_args_list:
            if call[0][0] == "send_message":
                send_msg_func = call[0][1]
                break
        
        # Test sending message without token
        result = await send_msg_func(channel="#general", text="Hello")
        
        assert "❌ Configuration Error" in result
        assert "No token configured" in result

