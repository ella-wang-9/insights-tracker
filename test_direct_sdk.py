#!/usr/bin/env python3
"""Test Databricks SDK directly with proper error handling."""

import os
import sys
import time

# Set environment variables first
os.environ['DATABRICKS_HOST'] = os.getenv('DATABRICKS_HOST', '')
os.environ['DATABRICKS_TOKEN'] = os.getenv('DATABRICKS_TOKEN', '')

print(f"Host: {os.environ.get('DATABRICKS_HOST', 'NOT SET')}")
print(f"Token: {'SET' if os.environ.get('DATABRICKS_TOKEN') else 'NOT SET'}")

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

try:
    print("\nInitializing client...")
    client = WorkspaceClient()
    print("✅ Client initialized")
    
    # Test the smallest, fastest model
    endpoint = "databricks-meta-llama-3-1-8b-instruct"
    
    messages = [ChatMessage(
        role=ChatMessageRole.USER,
        content="Reply with just: yes"
    )]
    
    print(f"\nTesting {endpoint}...")
    start = time.time()
    
    # Add timeout using signal
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Request timed out")
    
    # Set 30 second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)
    
    try:
        response = client.serving_endpoints.query(
            name=endpoint,
            messages=messages,
            max_tokens=5,
            temperature=0.0
        )
        
        # Cancel the alarm
        signal.alarm(0)
        
        elapsed = time.time() - start
        print(f"\n✅ Response in {elapsed:.1f}s")
        
        if response.choices:
            print(f"Response: {response.choices[0].message.content}")
        
    except TimeoutError:
        elapsed = time.time() - start
        print(f"\n❌ Timeout after {elapsed:.1f}s")
    except Exception as e:
        elapsed = time.time() - start
        print(f"\n❌ Error after {elapsed:.1f}s: {e}")
        
        # Check if it's a rate limit
        if "REQUEST_LIMIT_EXCEEDED" in str(e):
            print("\n⚠️  Rate limit detected. Waiting 30 seconds...")
            time.sleep(30)
            
            print("Retrying...")
            try:
                signal.alarm(30)
                response = client.serving_endpoints.query(
                    name=endpoint,
                    messages=messages,
                    max_tokens=5,
                    temperature=0.0
                )
                signal.alarm(0)
                
                if response.choices:
                    print(f"✅ Retry successful: {response.choices[0].message.content}")
            except Exception as e2:
                print(f"❌ Retry failed: {e2}")
                
except Exception as e:
    print(f"\n❌ Failed to initialize: {e}")