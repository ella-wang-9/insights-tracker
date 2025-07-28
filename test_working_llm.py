#!/usr/bin/env python3
"""Quick test to find a working LLM endpoint."""

import os
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

# Load environment
os.environ['DATABRICKS_HOST'] = os.getenv('DATABRICKS_HOST', '')
os.environ['DATABRICKS_TOKEN'] = os.getenv('DATABRICKS_TOKEN', '')

def test_endpoint(endpoint_name):
    """Test a specific endpoint."""
    try:
        client = WorkspaceClient()
        
        messages = [ChatMessage(
            role=ChatMessageRole.USER, 
            content="Say just 'yes' if you can hear me."
        )]
        
        print(f"Testing {endpoint_name}...", end="", flush=True)
        
        response = client.serving_endpoints.query(
            name=endpoint_name,
            messages=messages,
            max_tokens=10,
            temperature=0.1
        )
        
        if response.choices and len(response.choices) > 0:
            result = response.choices[0].message.content
            print(f" ✅ Works! Response: {result}")
            return True
        else:
            print(f" ❌ No response")
            return False
            
    except Exception as e:
        print(f" ❌ Error: {str(e)[:80]}")
        return False

# Test the endpoints we found
endpoints = [
    'databricks-meta-llama-3-1-8b-instruct',
    'llama-3-3-70b', 
    'databricks-meta-llama-3-3-70b-instruct',
    'meta_llama_3_70b_instruct-chat',
    'databricks-llama-4-maverick',
]

print("Testing LLM endpoints...")
print("=" * 60)

working = []
for endpoint in endpoints:
    if test_endpoint(endpoint):
        working.append(endpoint)
        break  # Stop at first working endpoint

if working:
    print(f"\n✅ Found working endpoint: {working[0]}")
    print("Use this in your code!")
else:
    print("\n❌ No working endpoints found")