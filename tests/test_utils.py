"""Unit tests for utility functions."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from slack_mcp.utils.client import (
    validate_slack_token,
    init_async_client,
    set_slack_client,
    get_slack_client
)
from slack_mcp.utils.errors import make_slack_request


class TestClientUtils:
    """Test cases for client utility functions."""
    
    def test_validate_slack_token_no_client(self):
        """Test validating token when no client is set."""
        # Clear any existing client
        set_slack_client(None)
        
        with pytest.raises(ValueError, match="No Slack token configured"):
            validate_slack_token()
    
    def test_validate_slack_token_with_client(self):
        """Test validating token when client is set."""
        mock_client = MagicMock(spec=WebClient)
        set_slack_client(mock_client)
        
        # Should not raise an exception
        validate_slack_token()
        
        # Clean up
        set_slack_client(None)
    
    def test_get_and_set_slack_client(self):
        """Test getting and setting the Slack client."""
        # Initially should be None
        assert get_slack_client() is None
        
        # Set a client
        mock_client = MagicMock(spec=WebClient)
        set_slack_client(mock_client)
        
        # Should return the same client
        assert get_slack_client() == mock_client
        
        # Clean up
        set_slack_client(None)
    
    @pytest.mark.asyncio
    async def test_init_async_client_success(self):
        """Test initializing async client successfully."""
        mock_client = MagicMock(spec=WebClient)
        mock_client.token = "xoxb-test-token"
        set_slack_client(mock_client)
        
        async_client = await init_async_client()
        assert async_client is not None
        assert async_client.token == "xoxb-test-token"
        
        # Clean up
        set_slack_client(None)
    
    @pytest.mark.asyncio
    async def test_init_async_client_no_token(self):
        """Test initializing async client without token."""
        set_slack_client(None)
        
        async_client = await init_async_client()
        assert async_client is None


class TestErrorUtils:
    """Test cases for error handling utilities."""
    
    @pytest.mark.asyncio
    async def test_make_slack_request_success(self):
        """Test making a successful Slack API request."""
        mock_method = AsyncMock(return_value={"ok": True, "data": "test"})
        
        result = await make_slack_request(mock_method, arg1="value1")
        
        assert result == {"ok": True, "data": "test"}
        mock_method.assert_called_once_with(arg1="value1")
    
    @pytest.mark.asyncio
    async def test_make_slack_request_api_error(self):
        """Test handling Slack API errors."""
        mock_response = {"ok": False, "error": "channel_not_found"}
        mock_method = AsyncMock(side_effect=SlackApiError("Error", mock_response))
        
        result = await make_slack_request(mock_method, channel="C123")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_make_slack_request_general_error(self):
        """Test handling general errors."""
        mock_method = AsyncMock(side_effect=Exception("Network error"))
        
        result = await make_slack_request(mock_method)
        
        assert result is None
