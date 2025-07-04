"""
Error handling and rate limiting utilities for Slack MCP Server.
"""
import time
import asyncio
import logging
from typing import Dict, Any, Optional
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)

# Rate limiting tracking
last_api_call_time = 0.0
MIN_API_INTERVAL = 1.0  # Minimum seconds between API calls


async def rate_limit_check() -> None:
    """Implement rate limiting compliance with async delays."""
    global last_api_call_time
    
    current_time = time.time()
    time_since_last_call = current_time - last_api_call_time
    
    if time_since_last_call < MIN_API_INTERVAL:
        sleep_time = MIN_API_INTERVAL - time_since_last_call
        logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
        await asyncio.sleep(sleep_time)
    
    last_api_call_time = time.time()


async def make_slack_request(client_method, **kwargs) -> Optional[Dict[str, Any]]:
    """Helper function for API requests with error handling and rate limiting."""
    try:
        # Apply rate limiting
        await rate_limit_check()
        
        # Make the API request
        response = await client_method(**kwargs)
        
        if response.get("ok"):
            return response
        else:
            logger.error(f"Slack API error: {response.get('error', 'Unknown error')}")
            return None
            
    except SlackApiError as e:
        logger.error(f"Slack API error: {e.response['error']}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in API request: {str(e)}")
        return None
