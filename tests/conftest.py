"""Pytest configuration and shared fixtures."""

import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from slack_sdk import WebClient
from slack_sdk.web.async_client import AsyncWebClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_slack_client():
    """Mock Slack WebClient for testing."""
    client = MagicMock(spec=WebClient)
    client.auth_test.return_value = {
        "ok": True,
        "url": "https://test.slack.com/",
        "team": "Test Team",
        "user": "test_user",
        "team_id": "T1234567890",
        "user_id": "U1234567890",
        "bot_id": "B1234567890"
    }
    return client


@pytest_asyncio.fixture
async def mock_async_slack_client():
    """Mock Async Slack WebClient for testing."""
    client = AsyncMock(spec=AsyncWebClient)
    client.auth_test.return_value = {
        "ok": True,
        "url": "https://test.slack.com/",
        "team": "Test Team", 
        "user": "test_user",
        "team_id": "T1234567890",
        "user_id": "U1234567890",
        "bot_id": "B1234567890"
    }
    return client


@pytest.fixture
def mock_mcp_server():
    """Mock MCP server instance."""
    server = MagicMock()
    server.tool = MagicMock()
    return server


@pytest.fixture
def sample_channel_response():
    """Sample channel response from Slack API."""
    return {
        "ok": True,
        "channel": {
            "id": "C1234567890",
            "name": "general",
            "is_channel": True,
            "is_group": False,
            "is_im": False,
            "is_mpim": False,
            "is_private": False,
            "created": 1360782804,
            "is_archived": False,
            "is_general": True,
            "unlinked": 0,
            "name_normalized": "general",
            "is_shared": False,
            "is_org_shared": False,
            "is_member": True,
            "is_pending_ext_shared": False,
            "pending_shared": [],
            "context_team_id": "T1234567890",
            "parent_conversation": None,
            "creator": "U1234567890",
            "is_ext_shared": False,
            "shared_team_ids": ["T1234567890"],
            "pending_connected_team_ids": [],
            "topic": {
                "value": "Company-wide announcements and work-based matters",
                "creator": "U1234567890",
                "last_set": 1360782804
            },
            "purpose": {
                "value": "This channel is for team-wide communication and announcements.",
                "creator": "U1234567890", 
                "last_set": 1360782804
            },
            "num_members": 100
        }
    }


@pytest.fixture
def sample_user_response():
    """Sample user response from Slack API."""
    return {
        "ok": True,
        "user": {
            "id": "U1234567890",
            "team_id": "T1234567890",
            "name": "test_user",
            "deleted": False,
            "color": "9f69e7",
            "real_name": "Test User",
            "tz": "America/Los_Angeles",
            "tz_label": "Pacific Standard Time",
            "tz_offset": -28800,
            "profile": {
                "avatar_hash": "g1234567890",
                "status_text": "Working from home",
                "status_emoji": ":house_with_garden:",
                "real_name": "Test User",
                "display_name": "testuser",
                "real_name_normalized": "Test User",
                "display_name_normalized": "testuser",
                "email": "test@example.com",
                "image_original": "https://avatars.slack-edge.com/test_original.jpg",
                "image_24": "https://avatars.slack-edge.com/test_24.jpg",
                "image_32": "https://avatars.slack-edge.com/test_32.jpg",
                "image_48": "https://avatars.slack-edge.com/test_48.jpg",
                "image_72": "https://avatars.slack-edge.com/test_72.jpg",
                "image_192": "https://avatars.slack-edge.com/test_192.jpg",
                "image_512": "https://avatars.slack-edge.com/test_512.jpg",
                "team": "T1234567890"
            },
            "is_admin": False,
            "is_owner": False,
            "is_primary_owner": False,
            "is_restricted": False,
            "is_ultra_restricted": False,
            "is_bot": False,
            "is_app_user": False,
            "updated": 1234567890
        }
    }


@pytest.fixture
def sample_message_response():
    """Sample message response from Slack API."""
    return {
        "ok": True,
        "channel": "C1234567890",
        "ts": "1234567890.123456",
        "message": {
            "bot_id": "B1234567890",
            "type": "message",
            "text": "Hello, World!",
            "user": "U1234567890",
            "ts": "1234567890.123456",
            "team": "T1234567890",
            "bot_profile": {
                "id": "B1234567890",
                "deleted": False,
                "name": "Test Bot",
                "updated": 1234567890,
                "app_id": "A1234567890",
                "icons": {
                    "image_36": "https://a.slack-edge.com/test_36.png",
                    "image_48": "https://a.slack-edge.com/test_48.png",
                    "image_72": "https://a.slack-edge.com/test_72.png"
                },
                "team_id": "T1234567890"
            }
        }
    }
