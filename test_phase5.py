#!/usr/bin/env python3
"""Test script for Phase 5 Channel Management Tools."""

import subprocess
import json
import sys
import time
from typing import Dict, Any, Optional

def call_mcp_tool(tool_name: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Call an MCP tool and return the parsed response."""
    mcp_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": params
        },
        "id": 1
    }
    
    cmd = ["docker", "run", "--rm", "-i", 
           "-e", "SLACK_BOT_TOKEN",
           "slack-mcp:latest"]
    
    try:
        # Send request
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, text=True)
        stdout, stderr = proc.communicate(input=json.dumps(mcp_request))
        
        # Parse response
        for line in stdout.split('\n'):
            if line.strip() and line.startswith('{'):
                try:
                    response = json.loads(line)
                    if response.get("result"):
                        return response["result"]
                except json.JSONDecodeError:
                    continue
        
        print(f"Error calling {tool_name}: No valid response")
        if stderr:
            print(f"Stderr: {stderr}")
        return None
        
    except Exception as e:
        print(f"Error calling {tool_name}: {e}")
        return None

def test_phase5_tools():
    """Test all Phase 5 Channel Management tools."""
    print("=== Testing Phase 5: Channel Management Tools ===\n")
    
    # Test 1: Create a test channel
    print("1. Testing create_channel...")
    channel_name = f"test-mcp-{int(time.time())}"
    result = call_mcp_tool("create_channel", {
        "name": channel_name,
        "is_private": False,
        "description": "Test channel created by MCP Phase 5 testing"
    })
    
    if result and result.get("success", False):
        print("✅ Channel created successfully!")
        channel_id = None
        # Extract channel ID from the result content
        content = result.get("content", [])
        if content and isinstance(content[0], dict):
            text = content[0].get("text", "")
            # Parse channel ID from the formatted output
            for line in text.split('\n'):
                if "• **ID:**" in line:
                    channel_id = line.split("**ID:**")[1].strip()
                    break
        
        if channel_id:
            print(f"   Channel ID: {channel_id}\n")
            
            # Test 2: Set channel topic
            print("2. Testing set_channel_topic...")
            result = call_mcp_tool("set_channel_topic", {
                "channel": channel_id,
                "topic": "Phase 5 Testing - Channel Management Tools"
            })
            if result and result.get("success", False):
                print("✅ Channel topic set successfully!\n")
            else:
                print("❌ Failed to set channel topic\n")
            
            # Test 3: Set channel purpose
            print("3. Testing set_channel_purpose...")
            result = call_mcp_tool("set_channel_purpose", {
                "channel": channel_id,
                "purpose": "This channel is used for testing Phase 5 channel management tools"
            })
            if result and result.get("success", False):
                print("✅ Channel purpose set successfully!\n")
            else:
                print("❌ Failed to set channel purpose\n")
            
            # Test 4: Join channel (bot should already be in it)
            print("4. Testing join_channel...")
            result = call_mcp_tool("join_channel", {
                "channel": channel_id
            })
            if result:
                print("✅ Join channel completed (bot may already be a member)\n")
            
            # Test 5: List channel members
            print("5. Testing list_channel_members...")
            result = call_mcp_tool("list_channel_members", {
                "channel": channel_id,
                "limit": 10
            })
            if result and result.get("success", False):
                print("✅ Channel members listed successfully!\n")
            else:
                print("❌ Failed to list channel members\n")
            
            # Test 6: Archive the channel
            print("6. Testing archive_channel...")
            result = call_mcp_tool("archive_channel", {
                "channel": channel_id
            })
            if result and result.get("success", False):
                print("✅ Channel archived successfully!\n")
            else:
                print("❌ Failed to archive channel\n")
            
            # Test 7: Unarchive the channel
            print("7. Testing unarchive_channel...")
            result = call_mcp_tool("unarchive_channel", {
                "channel": channel_id
            })
            if result and result.get("success", False):
                print("✅ Channel unarchived successfully!\n")
            else:
                print("❌ Failed to unarchive channel\n")
            
            # Test 8: Leave channel (then rejoin for cleanup)
            print("8. Testing leave_channel...")
            result = call_mcp_tool("leave_channel", {
                "channel": channel_id
            })
            if result and result.get("success", False):
                print("✅ Left channel successfully!\n")
                
                # Rejoin to be able to archive it
                print("   Rejoining channel for cleanup...")
                call_mcp_tool("join_channel", {"channel": channel_id})
            else:
                print("❌ Failed to leave channel\n")
            
            # Final cleanup: Archive the test channel
            print("9. Cleanup: Archiving test channel...")
            result = call_mcp_tool("archive_channel", {
                "channel": channel_id
            })
            if result and result.get("success", False):
                print("✅ Test channel archived for cleanup!\n")
            else:
                print("⚠️  Could not archive test channel\n")
                
        else:
            print("❌ Could not extract channel ID from creation response\n")
    else:
        print("❌ Failed to create test channel\n")
    
    # Test invite/remove functionality with existing channel
    print("10. Testing invite_to_channel and remove_from_channel...")
    print("    (Requires an existing channel and user IDs - skipping in automated test)\n")
    
    print("=== Phase 5 Testing Complete ===")
    print("\nSummary:")
    print("- Created test channel")
    print("- Set topic and purpose")
    print("- Joined/left channel")
    print("- Listed members")
    print("- Archived/unarchived channel")
    print("- Cleaned up test channel")
    print("\nNote: invite_to_channel and remove_from_channel require")
    print("specific user IDs and permissions, best tested manually.")

if __name__ == "__main__":
    test_phase5_tools()
