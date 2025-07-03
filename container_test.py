#!/usr/bin/env python3
"""Test script to verify MCP server functionality in container."""

import asyncio
import sys
sys.path.append('/app')

from src.slack_mcp_server import mcp

async def test_container():
    """Test MCP server in container."""
    print("🐳 Testing FastMCP Slack Server in Container")
    print("=" * 50)
    
    try:
        # Test tool registration
        tools_response = await mcp.list_tools()
        
        # Handle different response formats
        if isinstance(tools_response, dict) and 'tools' in tools_response:
            tools = tools_response['tools']
        elif isinstance(tools_response, list):
            tools = tools_response
        else:
            # Try to access tools attribute
            tools = getattr(tools_response, 'tools', tools_response)
        
        print(f"✅ Container tools: {len(tools)} tools registered")
        
        # List all tools
        for i, tool in enumerate(tools, 1):
            if hasattr(tool, 'name'):
                tool_name = tool.name
            elif isinstance(tool, dict):
                tool_name = tool.get('name', 'Unknown')
            else:
                tool_name = str(tool)
            print(f"  {i:2d}. {tool_name}")
        
        print("\n✅ Container Phase 2 verification successful!")
        return True
        
    except Exception as e:
        print(f"❌ Container test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_container())
    sys.exit(0 if success else 1)
