#!/usr/bin/env python3
"""
Test script for Phase 6: User Management Tools
Tests all user management functionality
"""

import asyncio
import os
import sys
from datetime import datetime
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from slack_mcp_server import (
    init_async_client,
    get_user_info,
    list_workspace_members,
    search_users,
    get_user_presence,
    get_user_timezone,
    set_user_status,
    update_user_profile,
    get_user_conversations,
    set_user_presence
)

class TestPhase6:
    def __init__(self):
        self.user_id = None  # Will be set during testing
        self.bot_user_id = None
        
    async def test_get_user_info(self):
        """Test getting user information"""
        print("\n=== Testing Get User Info ===")
        
        # First, get our bot's user ID
        client = await init_async_client()
        auth_response = await client.auth_test()
        self.bot_user_id = auth_response.get('user_id')
        
        if self.bot_user_id:
            result = await get_user_info(self.bot_user_id)
            print(result)
            
            # Store a user ID for other tests (use bot user for testing)
            self.user_id = self.bot_user_id
        else:
            print("❌ Could not get bot user ID")
    
    async def test_list_workspace_members(self):
        """Test listing workspace members"""
        print("\n=== Testing List Workspace Members ===")
        
        # Test with default limit
        result = await list_workspace_members()
        print(result)
        
        # Test with smaller limit
        print("\n--- With limit of 10 ---")
        result = await list_workspace_members(limit=10)
        print(result)
    
    async def test_search_users(self):
        """Test searching for users"""
        print("\n=== Testing Search Users ===")
        
        # Search for bot user
        print("--- Searching for 'bot' ---")
        result = await search_users("bot")
        print(result)
        
        # Search for admin
        print("\n--- Searching for 'admin' ---")
        result = await search_users("admin")
        print(result)
        
        # Search that likely won't find anything
        print("\n--- Searching for 'xyz123unlikely' ---")
        result = await search_users("xyz123unlikely")
        print(result)
    
    async def test_get_user_presence(self):
        """Test getting user presence"""
        print("\n=== Testing Get User Presence ===")
        
        if self.user_id:
            result = await get_user_presence(self.user_id)
            print(result)
        else:
            print("❌ No user ID available for testing")
    
    async def test_get_user_timezone(self):
        """Test getting user timezone"""
        print("\n=== Testing Get User Timezone ===")
        
        if self.user_id:
            result = await get_user_timezone(self.user_id)
            print(result)
        else:
            print("❌ No user ID available for testing")
    
    async def test_user_status_operations(self):
        """Test user status operations (requires user token)"""
        print("\n=== Testing User Status Operations ===")
        print("Note: These operations require a user token (xoxp-), not a bot token")
        
        # Test setting status
        print("--- Testing Set User Status ---")
        result = await set_user_status(
            status_text="Testing MCP Server",
            status_emoji=":computer:",
            expiration=0
        )
        print(result)
        
        # Test clearing status
        await asyncio.sleep(2)
        print("\n--- Testing Clear User Status ---")
        result = await set_user_status(
            status_text="",
            status_emoji="",
            expiration=0
        )
        print(result)
    
    async def test_update_user_profile(self):
        """Test updating user profile (requires user token)"""
        print("\n=== Testing Update User Profile ===")
        print("Note: This operation requires a user token (xoxp-), not a bot token")
        
        result = await update_user_profile(
            title="MCP Test User",
            display_name="MCP Tester"
        )
        print(result)
    
    async def test_get_user_conversations(self):
        """Test getting user conversations"""
        print("\n=== Testing Get User Conversations ===")
        
        # Test with all types
        print("--- All conversation types ---")
        result = await get_user_conversations()
        print(result)
        
        # Test with only channels
        print("\n--- Only channels ---")
        result = await get_user_conversations(
            types="public_channel,private_channel",
            limit=20
        )
        print(result)
    
    async def test_set_user_presence(self):
        """Test setting user presence (requires user token)"""
        print("\n=== Testing Set User Presence ===")
        print("Note: This operation requires a user token (xoxp-), not a bot token")
        
        # Test setting to away
        print("--- Setting presence to away ---")
        result = await set_user_presence("away")
        print(result)
        
        # Test setting back to active
        await asyncio.sleep(2)
        print("\n--- Setting presence to active ---")
        result = await set_user_presence("active")
        print(result)
    
    async def run_all_tests(self):
        """Run all Phase 6 tests"""
        print("=" * 60)
        print("PHASE 6: USER MANAGEMENT TOOLS - TEST SUITE")
        print("=" * 60)
        
        # Tests that work with bot tokens
        await self.test_get_user_info()
        await asyncio.sleep(1)
        
        await self.test_list_workspace_members()
        await asyncio.sleep(1)
        
        await self.test_search_users()
        await asyncio.sleep(1)
        
        await self.test_get_user_presence()
        await asyncio.sleep(1)
        
        await self.test_get_user_timezone()
        await asyncio.sleep(1)
        
        await self.test_get_user_conversations()
        await asyncio.sleep(1)
        
        # Tests that require user tokens
        print("\n" + "=" * 60)
        print("USER TOKEN REQUIRED TESTS")
        print("The following tests require a user token (xoxp-)")
        print("They will likely fail with a bot token")
        print("=" * 60)
        
        await self.test_user_status_operations()
        await asyncio.sleep(1)
        
        await self.test_update_user_profile()
        await asyncio.sleep(1)
        
        await self.test_set_user_presence()
        
        print("\n" + "=" * 60)
        print("PHASE 6 TESTING COMPLETE")
        print("=" * 60)

async def main():
    # Check for Slack token
    if not os.getenv('SLACK_BOT_TOKEN'):
        print("❌ Error: SLACK_BOT_TOKEN environment variable not set")
        print("Please set your Slack bot token before running tests")
        return
    
    # Run tests
    tester = TestPhase6()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
