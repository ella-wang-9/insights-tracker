#!/usr/bin/env python3
"""Test Databricks LLM endpoint availability and response times."""

import os
import time
import asyncio
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

# Ensure environment variables are set
os.environ['DATABRICKS_HOST'] = os.getenv('DATABRICKS_HOST', '')
os.environ['DATABRICKS_TOKEN'] = os.getenv('DATABRICKS_TOKEN', '')

async def test_endpoint(client, endpoint_name, test_prompt):
    """Test a single endpoint."""
    print(f"\nTesting endpoint: {endpoint_name}")
    print("-" * 50)
    
    try:
        messages = [ChatMessage(role=ChatMessageRole.USER, content=test_prompt)]
        
        start_time = time.time()
        print("  Sending request...")
        
        # Use asyncio with timeout
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.serving_endpoints.query,
                name=endpoint_name,
                messages=messages,
                max_tokens=100,
                temperature=0.1
            ),
            timeout=30.0
        )
        
        elapsed = time.time() - start_time
        
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            print(f"  ✅ Success in {elapsed:.1f} seconds")
            print(f"  Response preview: {content[:100]}...")
            return True, elapsed
        else:
            print(f"  ❌ No response content")
            return False, elapsed
            
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"  ❌ Timeout after {elapsed:.1f} seconds")
        return False, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)[:200]
        print(f"  ❌ Error after {elapsed:.1f} seconds: {error_msg}")
        return False, elapsed

async def check_all_endpoints():
    """Check all potentially available endpoints."""
    print("=" * 80)
    print("Databricks LLM Endpoint Availability Test")
    print("=" * 80)
    
    # Initialize client
    try:
        client = WorkspaceClient()
        print("✅ Databricks client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Databricks client: {e}")
        return
    
    # List of endpoints to test
    endpoints = [
        "llama_3_1_70b",
        "meta_llama_3_70b_instruct-chat", 
        "databricks-meta-llama-3-1-8b-instruct",
        "databricks-meta-llama-3-1-70b-instruct",
        "databricks-dbrx-instruct",
        "databricks-mixtral-8x7b-instruct",
        "databricks-llama-2-70b-chat"
    ]
    
    # Simple test prompt
    test_prompt = "Extract the company name from this text: ACME Corp needs AI solutions. Return only the company name."
    
    results = []
    
    for endpoint in endpoints:
        success, elapsed = await test_endpoint(client, endpoint, test_prompt)
        results.append((endpoint, success, elapsed))
        
        # Small delay between tests
        if success:
            await asyncio.sleep(1)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    working_endpoints = []
    for endpoint, success, elapsed in results:
        status = "✅" if success else "❌"
        print(f"{status} {endpoint:<40} {elapsed:>6.1f}s")
        if success:
            working_endpoints.append((endpoint, elapsed))
    
    if working_endpoints:
        print(f"\nWorking endpoints: {len(working_endpoints)}/{len(endpoints)}")
        print("\nFastest endpoints:")
        for endpoint, elapsed in sorted(working_endpoints, key=lambda x: x[1])[:3]:
            print(f"  - {endpoint}: {elapsed:.1f}s")
    else:
        print("\n⚠️  No working endpoints found!")
        print("\nPossible issues:")
        print("- Check DATABRICKS_HOST and DATABRICKS_TOKEN are set correctly")
        print("- Verify you have access to foundation model endpoints")
        print("- Check if endpoints are in READY state")
        print("- Rate limits may be affecting access")

async def test_with_retries():
    """Test endpoints with retry logic."""
    print("\n" + "=" * 80)
    print("Testing with Retry Logic")
    print("=" * 80)
    
    try:
        client = WorkspaceClient()
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return
    
    # Test the most likely working endpoint with retries
    endpoint = "databricks-meta-llama-3-1-70b-instruct"
    test_prompt = "What is 2+2? Return only the number."
    
    for attempt in range(3):
        print(f"\nAttempt {attempt + 1}/3 for {endpoint}")
        success, elapsed = await test_endpoint(client, endpoint, test_prompt)
        
        if success:
            print(f"✅ Success on attempt {attempt + 1}")
            break
        else:
            if attempt < 2:
                wait_time = (attempt + 1) * 5
                print(f"Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)

async def main():
    """Run all tests."""
    await check_all_endpoints()
    await test_with_retries()

if __name__ == "__main__":
    # Run with proper event loop
    asyncio.run(main())