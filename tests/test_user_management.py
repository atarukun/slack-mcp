"""Unit tests for user management tools."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from slack_sdk.errors import SlackApiError

from slack_mcp.tools import user_management


class TestUserManagementTools:
    """Test cases for user management Slack MCP tools."""
    
    def test_register_tools(self, mock_mcp_server):
        """Test that all user management tools are properly registered."""
        user_management.register_tools(mock_mcp_server)
        
        # Verify tool decorator was called for each tool
        assert mock_mcp_server.tool.call_count >= 4  # At least 4 user management tools
        
        # Check that specific tools were registered
        tool_names = [call[0][0] for call in mock_mcp_server.tool.call_args_list]
        expected_tools = [
            "list_workspace_members",
            "get_user_presence",
            "get_user_timezone",
            "search_slack_users"
        ]
        for tool in expected_tools:
            assert tool in tool_names
    
    @pytest.mark.asyncio
    @patch('slack_mcp.tools.user_management.init_async_client')
    @patch('slack_mcp.tools.user_management.make_slack_request')
    @patch('slack_mcp.tools.user_management.validate_slack_token')
    async def test_list_workspace_members_success(self, mock_validate, mock_make_request, mock_init_client, mock_mcp_server):
        """Test listing workspace members successfully."""
        # Setup mocks
        mock_validate.return_value = None
        mock_async_client = AsyncMock()
        mock_init_client.return_value = mock_async_client
        
        mock_make_request.return_value = {
            "ok": True,
            "members": [
                {
                    "id": "U123",
                    "name": "testuser1",
                    "real_name": "Test User 1",
                    "is_bot": False,
                    "is_admin": False
                },
                {
                    "id": "U456",
                    "name": "testuser2",
                    "real_name": "Test User 2",
                    "is_bot": False,
                    "is_admin": True
                }
            ]
        }
        
        # Register tools and get the function
        user_management.register_tools(mock_mcp_server)
        list_members_func = None
        for call in mock_mcp_server.tool.call_args_list:
            if call[0][0] == "list_workspace_members":
                list_members_func = call[0][1]
                break
        
        # Test listing members
        result = await list_members_func(limit=100)
        
        assert "👥 **Workspace Members**" in result
        assert "Total members: 2" in result
        assert "Test User 1" in result
        assert "Test User 2" in result
    
    @pytest.mark.asyncio
    @patch('slack_mcp.tools.user_management.init_async_client')
    @patch('slack_mcp.tools.user_management.make_slack_request')
    @patch('slack_mcp.tools.user_management.validate_slack_token')
    async def test_get_user_presence_success(self, mock_validate, mock_make_request, mock_init_client, mock_mcp_server):
        """Test getting user presence successfully."""
        # Setup mocks
        mock_validate.return_value = None
        mock_async_client = AsyncMock()
        mock_init_client.return_value = mock_async_client
        
        mock_make_request.return_value = {
            "ok": True,
            "presence": "active",
            "online": True,
            "auto_away": False,
            "manual_away": False,
            "connection_count": 1,
            "last_activity": 1234567890
        }
        
        # Register tools and get the function
        user_management.register_tools(mock_mcp_server)
        get_presence_func = None
        for call in mock_mcp_server.tool.call_args_list:
            if call[0][0] == "get_user_presence":
                get_presence_func = call[0][1]
                break
        
        # Test getting presence
        result = await get_presence_func(user="U123")
        
        assert "🟢 **User Presence**" in result
        assert "Status: active" in result
        assert "Online: Yes" in result
    
    @pytest.mark.asyncio
    @patch('slack_mcp.tools.user_management.init_async_client')
    @patch('slack_mcp.tools.user_management.make_slack_request')
    @patch('slack_mcp.tools.user_management.validate_slack_token')
    async def test_search_slack_users_success(self, mock_validate, mock_make_request, mock_init_client, mock_mcp_server):
        """Test searching for users successfully."""
        # Setup mocks
        mock_validate.return_value = None
        mock_async_client = AsyncMock()
        mock_init_client.return_value = mock_async_client
        
        # Mock users.list response for search
        mock_make_request.return_value = {
            "ok": True,
            "members": [
                {
                    "id": "U123",
                    "name": "john_doe",
                    "real_name": "John Doe",
                    "profile": {
                        "email": "john@example.com",
                        "display_name": "John"
                    },
                    "is_bot": False
                }
            ]
        }
        
        # Register tools and get the function
        user_management.register_tools(mock_mcp_server)
        search_users_func = None
        for call in mock_mcp_server.tool.call_args_list:
            if call[0][0] == "search_slack_users":
                search_users_func = call[0][1]
                break
        
        # Test searching users
        result = await search_users_func(query="john")
        
        assert "🔍 **Search Results**" in result
        assert "John Doe" in result
        assert "@john_doe" in result
