#!/usr/bin/env python3
"""
Test script for Phase 7: File Operations
Tests all file-related tools in the Slack MCP server
"""

import subprocess
import json
import sys
import time

def test_tool(tool_name, params=None):
    """Test a single MCP tool"""
    print(f"\n{'='*60}")
    print(f"Testing: {tool_name}")
    print(f"{'='*60}")
    
    cmd = [
        "npx", "@modelcontextprotocol/inspector", 
        "http://localhost:3006/tools/call",
        "--tool", tool_name
    ]
    
    if params:
        cmd.extend(["--params", json.dumps(params)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ SUCCESS")
            print(f"Output: {result.stdout}")
        else:
            print("❌ FAILED")
            print(f"Error: {result.stderr}")
            
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Test all Phase 7 file operation tools"""
    print("🧪 Testing Phase 7: File Operations Tools")
    print("=" * 60)
    
    # Test file ID - you'll need to replace this with an actual file ID from your workspace
    test_file_id = "F123456789"  # Replace with actual file ID
    test_channel = "C123456789"  # Replace with actual channel ID
    test_user = "U123456789"     # Replace with actual user ID
    
    tests = [
        # Enhanced upload_file (to channel)
        ("upload_file", {
            "channels": test_channel,
            "content": "This is a test file for Phase 7 testing",
            "filename": "phase7_test.txt",
            "filetype": "text",
            "title": "Phase 7 Test File",
            "initial_comment": "Testing enhanced file upload to channel"
        }),
        
        # New upload_file_to_user
        ("upload_file_to_user", {
            "user": test_user,
            "content": "This is a direct message file test",
            "filename": "dm_test.txt",
            "filetype": "text",
            "title": "DM Test File",
            "initial_comment": "Testing file upload to user"
        }),
        
        # List files
        ("list_files", {
            "count": 10,
            "page": 1
        }),
        
        # List files with filters
        ("list_files", {
            "types": "images,pdfs",
            "user": test_user,
            "count": 5
        }),
        
        # Get file info
        ("get_file_info", {
            "file_id": test_file_id
        }),
        
        # Get file content
        ("get_file_content", {
            "file_id": test_file_id,
            "max_size_mb": 5.0
        }),
        
        # Share file
        ("share_file", {
            "file_id": test_file_id,
            "channels": test_channel,
            "comment": "Sharing this file for testing purposes"
        }),
        
        # Delete file (commented out to avoid deleting actual files)
        # ("delete_file", {
        #     "file_id": test_file_id
        # }),
    ]
    
    results = []
    for tool_name, params in tests:
        success = test_tool(tool_name, params)
        results.append((tool_name, success))
        time.sleep(2)  # Rate limiting
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    for tool_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{tool_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All Phase 7 tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
