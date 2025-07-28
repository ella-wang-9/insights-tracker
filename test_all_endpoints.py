#!/usr/bin/env python3
"""Test all available chat endpoints to find working ones."""

import os
import sys
import json
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

# Common foundation model endpoint patterns
ENDPOINT_PATTERNS = [
    # Databricks-hosted models
    'databricks-dbrx-instruct',
    'databricks-llama-2-70b-chat',
    'databricks-mixtral-8x7b-instruct',
    'databricks-mpt-30b-instruct',
    'databricks-llama-2-7b-chat',
    
    # Meta Llama models
    'llama-2-70b-chat',
    'llama-2-7b-chat',
    'llama-3-70b-instruct',
    'llama-3-8b-instruct',
    'meta-llama-3-70b-instruct',
    
    # Other common patterns
    'mixtral-8x7b-instruct',
    'dbrx-instruct',
    'mpt-30b-instruct',
    'mpt-7b-instruct',
    
    # From the list we found
    'databricks-meta-llama-3-1-8b-instruct',
    'llama_3_1_70b',
    'meta_llama_3_70b_instruct-chat',
    'databricks-meta-llama-3-3-70b-instruct',
]

def test_endpoint(client, endpoint_name):
    """Test a specific endpoint."""
    try:
        print(f"  Testing: {endpoint_name}...", end="", flush=True)
        
        messages = [ChatMessage(
            role=ChatMessageRole.USER, 
            content="Reply with just 'yes' if you can hear me."
        )]
        
        response = client.serving_endpoints.query(
            name=endpoint_name,
            messages=messages,
            max_tokens=10,
            temperature=0.1
        )
        
        if response.choices and len(response.choices) > 0:
            result = response.choices[0].message.content
            print(f" ✅ SUCCESS! Response: {result[:50]}")
            return True
        else:
            print(f" ❌ No response")
            return False
            
    except Exception as e:
        error_msg = str(e)[:100]
        if 'not found' in error_msg.lower():
            print(f" ❌ Not found")
        elif 'access denied' in error_msg.lower():
            print(f" ❌ Access denied")
        elif 'timeout' in error_msg.lower():
            print(f" ❌ Timeout")
        else:
            print(f" ❌ Error: {error_msg}")
        return False

def main():
    """Test all endpoints."""
    print("Searching for working chat endpoints...")
    print("=" * 60)
    
    try:
        client = WorkspaceClient()
        print("✅ Databricks client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return
    
    # First, list actual serving endpoints
    print("\nListing actual serving endpoints...")
    try:
        endpoints = list(client.serving_endpoints.list())
        chat_endpoints = []
        
        for endpoint in endpoints:
            if endpoint.state.ready == "READY":
                # Check if it might be a chat endpoint
                name_lower = endpoint.name.lower()
                if any(pattern in name_lower for pattern in ['llama', 'chat', 'instruct', 'dbrx', 'mixtral', 'mpt', 'gpt', 'claude']):
                    chat_endpoints.append(endpoint.name)
                    print(f"  Found potential chat endpoint: {endpoint.name}")
        
        print(f"\nFound {len(chat_endpoints)} potential chat endpoints")
        
        # Test the found endpoints
        if chat_endpoints:
            print("\nTesting found endpoints...")
            working = []
            for endpoint in chat_endpoints[:10]:  # Test up to 10
                if test_endpoint(client, endpoint):
                    working.append(endpoint)
        
    except Exception as e:
        print(f"Error listing endpoints: {e}")
        chat_endpoints = []
        working = []
    
    # Also test common patterns
    print("\nTesting common endpoint patterns...")
    pattern_working = []
    for endpoint in ENDPOINT_PATTERNS:
        if test_endpoint(client, endpoint):
            pattern_working.append(endpoint)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_working = list(set(working + pattern_working))
    
    if all_working:
        print(f"\n✅ Found {len(all_working)} working endpoints:")
        for ep in all_working:
            print(f"  - {ep}")
        
        print(f"\n📝 Recommended endpoints to use in order:")
        for i, ep in enumerate(all_working[:4], 1):
            print(f"  {i}. {ep}")
    else:
        print("\n❌ No working chat endpoints found!")
        print("\nPossible issues:")
        print("1. Authentication - check DATABRICKS_HOST and DATABRICKS_TOKEN")
        print("2. Permissions - ensure you have access to model serving endpoints")
        print("3. Network - check if you can access the Databricks workspace")

if __name__ == "__main__":
    main()