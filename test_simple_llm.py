#!/usr/bin/env python3
"""Test with a simple endpoint that should work."""

import os
import sys
import asyncio
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

async def test_endpoint_async(endpoint_name):
    """Test endpoint with timeout."""
    try:
        client = WorkspaceClient()
        
        messages = [ChatMessage(
            role=ChatMessageRole.USER, 
            content="Reply with the number 5."
        )]
        
        print(f"Testing {endpoint_name}...")
        
        # Create async wrapper
        async def query():
            return await asyncio.to_thread(
                client.serving_endpoints.query,
                name=endpoint_name,
                messages=messages,
                max_tokens=10,
                temperature=0.0
            )
        
        # Try with 10 second timeout
        response = await asyncio.wait_for(query(), timeout=10.0)
        
        if response.choices and len(response.choices) > 0:
            result = response.choices[0].message.content
            print(f"✅ Success! Response: {result}")
            return True
        else:
            print(f"❌ No response")
            return False
            
    except asyncio.TimeoutError:
        print(f"❌ Timeout after 10 seconds")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
        return False

async def main():
    # Try the endpoints that showed as READY
    endpoints = [
        'llama_3_1_70b',  # This was in the READY list
        'meta_llama_3_70b_instruct-chat',  # This was in the READY list
        'databricks-meta-llama-3-1-8b-instruct',
    ]
    
    for endpoint in endpoints:
        if await test_endpoint_async(endpoint):
            print(f"\n✅ Working endpoint found: {endpoint}")
            print("Update your code to use this endpoint!")
            return
    
    print("\n❌ No working endpoints found")

if __name__ == "__main__":
    asyncio.run(main())