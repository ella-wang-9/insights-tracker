#!/usr/bin/env python3
"""Test the 8B model directly."""

import os
import time
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

# Set environment variables
os.environ['DATABRICKS_HOST'] = os.getenv('DATABRICKS_HOST', '')
os.environ['DATABRICKS_TOKEN'] = os.getenv('DATABRICKS_TOKEN', '')

print("Testing databricks-meta-llama-3-1-8b-instruct endpoint...")

try:
    client = WorkspaceClient()
    print("✅ Client initialized")
    
    # Very simple prompt
    messages = [ChatMessage(
        role=ChatMessageRole.USER, 
        content="What is 5+5? Reply with just the number."
    )]
    
    print("\nSending request...")
    start = time.time()
    
    response = client.serving_endpoints.query(
        name="databricks-meta-llama-3-1-8b-instruct",
        messages=messages,
        max_tokens=5,
        temperature=0.0
    )
    
    elapsed = time.time() - start
    print(f"\n✅ Response received in {elapsed:.1f} seconds")
    
    if response.choices:
        print(f"Response: {response.choices[0].message.content}")
    else:
        print("❌ No response content")
        
except Exception as e:
    print(f"\n❌ Error: {e}")