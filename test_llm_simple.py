#!/usr/bin/env python3
"""Simple test of Databricks LLM with minimal code."""

import os
os.environ['DATABRICKS_HOST'] = os.getenv('DATABRICKS_HOST', '')
os.environ['DATABRICKS_TOKEN'] = os.getenv('DATABRICKS_TOKEN', '')

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

print("Testing Databricks LLM endpoints...")

try:
    w = WorkspaceClient()
    
    # List of endpoints to try
    endpoints = [
        'databricks-meta-llama-3-1-8b-instruct',
        'qwen25-coder-7b-llama',
        'llama-3-3-70b',
    ]
    
    for endpoint in endpoints:
        print(f"\nTrying {endpoint}...")
        try:
            response = w.serving_endpoints.query(
                name=endpoint,
                messages=[ChatMessage(role=ChatMessageRole.USER, content="Say yes")],
                max_tokens=5,
                temperature=0.0
            )
            
            if response.choices:
                print(f"✅ SUCCESS! Response: {response.choices[0].message.content}")
                print(f"This endpoint works: {endpoint}")
                break
            else:
                print(f"❌ No response from {endpoint}")
                
        except Exception as e:
            error_msg = str(e)
            if "REQUEST_LIMIT_EXCEEDED" in error_msg:
                print(f"❌ Rate limited: {endpoint}")
            elif "timeout" in error_msg.lower():
                print(f"❌ Timeout: {endpoint}")
            else:
                print(f"❌ Error: {error_msg[:100]}")
                
except Exception as e:
    print(f"Failed to initialize: {e}")