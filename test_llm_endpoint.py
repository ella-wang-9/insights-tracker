#!/usr/bin/env python3
"""Test LLM endpoint connectivity directly."""

import os
import sys
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

# Test with environment variables
os.environ['DATABRICKS_HOST'] = os.getenv('DATABRICKS_HOST', '')
os.environ['DATABRICKS_TOKEN'] = os.getenv('DATABRICKS_TOKEN', '')

def test_endpoint(endpoint_name):
    """Test a specific endpoint."""
    print(f"\nTesting endpoint: {endpoint_name}")
    print("-" * 50)
    
    try:
        client = WorkspaceClient()
        
        # Simple test prompt
        messages = [ChatMessage(
            role=ChatMessageRole.USER, 
            content="What is 2+2? Reply with just the number."
        )]
        
        print(f"Sending request to {endpoint_name}...")
        response = client.serving_endpoints.query(
            name=endpoint_name,
            messages=messages,
            max_tokens=10,
            temperature=0.1
        )
        
        if response.choices and len(response.choices) > 0:
            result = response.choices[0].message.content
            print(f"✅ Success! Response: {result}")
            return True
        else:
            print(f"❌ No response choices received")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Test all endpoints."""
    endpoints = [
        'databricks-meta-llama-3-1-8b-instruct',
        'llama_3_1_70b',
        'meta_llama_3_70b_instruct-chat',
        'databricks-meta-llama-3-3-70b-instruct',
    ]
    
    print("Testing LLM Endpoints")
    print("=" * 50)
    print(f"Host: {os.getenv('DATABRICKS_HOST', 'Not set')}")
    print(f"Token: {'Set' if os.getenv('DATABRICKS_TOKEN') else 'Not set'}")
    
    working_endpoints = []
    
    for endpoint in endpoints:
        if test_endpoint(endpoint):
            working_endpoints.append(endpoint)
    
    print("\n" + "=" * 50)
    print(f"Summary: {len(working_endpoints)}/{len(endpoints)} endpoints working")
    if working_endpoints:
        print(f"Working endpoints: {', '.join(working_endpoints)}")
        print(f"\nRecommended primary endpoint: {working_endpoints[0]}")
    else:
        print("❌ No working endpoints found!")
        print("\nPossible issues:")
        print("1. Authentication - check DATABRICKS_HOST and DATABRICKS_TOKEN")
        print("2. Permissions - ensure you have access to model serving endpoints")
        print("3. Endpoint names - endpoints may have changed")

if __name__ == "__main__":
    main()