"""Integration tests for the entire Slack MCP server."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.mark.integration
class TestIntegrationSlackMCP:
    """Integration test cases for Slack MCP server functionality."""
    
    @pytest.mark.asyncio
    async def test_mcp_end_to_end(self, mock_mcp_server, mock_async_slack_client, sample_channel_response, sample_user_response, sample_message_response):
        """End-to-end integration test for the Slack MCP server."""
        
        # Assign mocked Slack client
        with patch('slack_mcp_server.mcp') as mcp_mock:
            with patch('slack_mcp_server.WebClient', return_value=mock_async_slack_client):
                # Initialize mocked Slack client
                from slack_mcp.utils.client import set_slack_client
                set_slack_client(mock_async_slack_client)
                
                # Setup mock responses
                mock_async_slack_client.conversations_info.return_value = sample_channel_response
                mock_async_slack_client.users_info.return_value = sample_user_response
                mock_async_slack_client.chat_postMessage.return_value = sample_message_response
                
                # ACT - Perform MCP operations
                core_tool_result = await mock_mcp_server.perform_tool_action('get_channel_info', channel='C1234567890')
                
                # ASSERT - Validate response of core tools
                assert "\u2714 **Channel Information**" in core_tool_result, "Channel information tool failed."
                assert "Channel ID: C1234567890" in core_tool_result
                assert "Channel Name: #general" in core_tool_result
                
                user_tool_result = await mock_mcp_server.perform_tool_action('get_user_info', user='U1234567890')
                assert "\u2714 **User Information**" in user_tool_result, "User information tool failed."
                assert "User ID: U1234567890" in user_tool_result
                assert "Real Name: Test User" in user_tool_result
                
                # Simulate sending a message
                message_tool_result = await mock_mcp_server.perform_tool_action(
                    'send_message', 
                    channel='C1234567890',
                    text="Test message sent during integration test"
                )
                assert "\u2714 **Message Sent Successfully**" in message_tool_result, "Message send tool failed."
                assert "Message: Test message sent during integration test" in message_tool_result
                assert "Channel: C1234567890" in message_tool_result
                
                # Ensure all tools were correctly triggered
                mcp_mock.perform_tool_action.assert_any_call('get_channel_info', channel='C1234567890')
                mcp_mock.perform_tool_action.assert_any_call('get_user_info', user='U1234567890')
                mcp_mock.perform_tool_action.assert_any_call('send_message', channel='C1234567890', text="Test message sent during integration test")
