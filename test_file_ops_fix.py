#!/usr/bin/env python3
"""Test script to validate fixes for file operations tools (Issue #30)"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from slack_mcp.utils import MIN_API_INTERVAL, rate_limit_check

# Test configuration
CHANNEL_ID = "C081C7XN02D"  # Test channel ID

async def test_file_operations():
    """Test file operations tools"""
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        print("❌ SLACK_BOT_TOKEN not set")
        return
    
    client = AsyncWebClient(token=token)
    
    print("🧪 Testing File Operations Tools\n")
    
    # First, upload a test file
    print("1️⃣ Uploading test file...")
    try:
        await rate_limit_check()
        upload_response = await client.files_upload_v2(
            channels=CHANNEL_ID,
            content="This is a test file for file operations.\nLine 2\nLine 3",
            filename="test_file_ops.txt",
            title="Test File Operations",
            initial_comment="Testing file operations"
        )
        
        if upload_response.get("ok"):
            file_id = upload_response["file"]["id"]
            print(f"✅ File uploaded successfully (ID: {file_id})")
        else:
            print(f"❌ Failed to upload file: {upload_response}")
            return
            
    except SlackApiError as e:
        print(f"❌ Error uploading file: {e.response['error']}")
        return
    
    await asyncio.sleep(2)  # Wait for file to be processed
    
    # Test list_files
    print("\n2️⃣ Testing list_files...")
    try:
        await rate_limit_check()
        list_response = await client.files_list(
            channel=CHANNEL_ID,
            count=10
        )
        
        if list_response.get("ok"):
            files = list_response.get("files", [])
            if files:
                print(f"✅ list_files returned {len(files)} file(s)")
                # Check if our uploaded file is in the list
                found = any(f["id"] == file_id for f in files)
                if found:
                    print("✅ Uploaded file found in list")
                else:
                    print("⚠️ Uploaded file not found in list (might be timing issue)")
            else:
                print("❌ list_files returned empty results")
        else:
            print(f"❌ Failed to list files: {list_response}")
            
    except SlackApiError as e:
        print(f"❌ Error listing files: {e.response['error']}")
    
    # Test get_file_info
    print("\n3️⃣ Testing get_file_info...")
    try:
        await rate_limit_check()
        info_response = await client.files_info(file=file_id)
        
        if info_response.get("ok"):
            file_info = info_response.get("file", {})
            print(f"✅ get_file_info returned file: {file_info.get('name')}")
            print(f"   Type: {file_info.get('filetype')}")
            print(f"   Size: {file_info.get('size')} bytes")
        else:
            print(f"❌ Failed to get file info: {info_response}")
            
    except SlackApiError as e:
        print(f"❌ Error getting file info: {e.response['error']}")
    
    # Test get_file_content  
    print("\n4️⃣ Testing get_file_content...")
    try:
        await rate_limit_check()
        # First get file info to get download URL
        info_response = await client.files_info(file=file_id)
        
        if info_response.get("ok"):
            download_url = info_response["file"].get("url_private_download")
            if download_url:
                import httpx
                headers = {
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "Slack-MCP-Server/1.0"
                }
                
                async with httpx.AsyncClient() as http_client:
                    response = await http_client.get(download_url, headers=headers)
                    if response.status_code == 200:
                        content = response.text
                        print(f"✅ get_file_content downloaded file ({len(content)} chars)")
                        print(f"   Content preview: {content[:50]}...")
                    else:
                        print(f"❌ Failed to download file: HTTP {response.status_code}")
            else:
                print("❌ No download URL available")
        else:
            print(f"❌ Failed to get file info for download: {info_response}")
            
    except Exception as e:
        print(f"❌ Error downloading file content: {str(e)}")
    
    # Test share_file
    print("\n5️⃣ Testing share_file...")
    try:
        await rate_limit_check()
        # First make the file public
        share_response = await client.files_sharedPublicURL(file=file_id)
        
        if share_response.get("ok"):
            public_url = share_response["file"].get("permalink_public")
            print(f"✅ Made file public: {public_url}")
            
            # Now share it by posting a message
            await rate_limit_check()
            msg_response = await client.chat_postMessage(
                channel=CHANNEL_ID,
                text=f"Shared file: test_file_ops.txt",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Shared file: *test_file_ops.txt*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"<{public_url}|View File>"
                        }
                    }
                ]
            )
            
            if msg_response.get("ok"):
                print("✅ share_file posted message with file link")
            else:
                print(f"❌ Failed to post share message: {msg_response}")
        else:
            print(f"❌ Failed to make file public: {share_response}")
            
    except SlackApiError as e:
        print(f"❌ Error sharing file: {e.response['error']}")
    
    # Clean up - delete the test file
    print("\n6️⃣ Cleaning up test file...")
    try:
        await rate_limit_check()
        delete_response = await client.files_delete(file=file_id)
        
        if delete_response.get("ok"):
            print("✅ Test file deleted successfully")
        else:
            print(f"⚠️ Failed to delete test file: {delete_response}")
            
    except SlackApiError as e:
        print(f"⚠️ Error deleting test file: {e.response['error']}")
    
    print("\n✅ File operations test completed!")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_file_operations())
