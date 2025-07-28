#!/usr/bin/env python3
"""Direct test of Databricks LLM endpoints."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.local')

# Set up environment variables
os.environ['DATABRICKS_HOST'] = os.getenv('DATABRICKS_HOST', '')
os.environ['DATABRICKS_TOKEN'] = os.getenv('DATABRICKS_TOKEN', '')

print(f"DATABRICKS_HOST: {os.environ.get('DATABRICKS_HOST')}")
print(f"DATABRICKS_TOKEN: {os.environ.get('DATABRICKS_TOKEN')[:10]}..." if os.environ.get('DATABRICKS_TOKEN') else "No token")

async def test_databricks_llm():
    """Test Databricks LLM endpoints directly."""
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
    
    try:
        # Initialize client
        client = WorkspaceClient()
        print("\nInitialized Databricks client successfully")
        
        # List available serving endpoints
        print("\nAvailable serving endpoints:")
        endpoints = client.serving_endpoints.list()
        for endpoint in endpoints:
            print(f"  - {endpoint.name} (state: {endpoint.state.ready if endpoint.state else 'Unknown'})")
        
        # Test endpoints
        test_endpoints = [
            'databricks-meta-llama-3-1-8b-instruct',
            'llama_3_1_70b',
            'meta_llama_3_70b_instruct-chat',
            'databricks-meta-llama-3-3-70b-instruct',
        ]
        
        test_prompt = "Extract the company name from this text: Meeting with ACME Corp on January 15th to discuss their product catalog needs."
        
        for endpoint_name in test_endpoints:
            print(f"\n\nTesting endpoint: {endpoint_name}")
            print("-" * 50)
            
            try:
                messages = [ChatMessage(role=ChatMessageRole.USER, content=test_prompt)]
                
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        client.serving_endpoints.query,
                        name=endpoint_name,
                        messages=messages,
                        max_tokens=200,
                        temperature=0.1
                    ),
                    timeout=30.0
                )
                
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    print(f"✓ Success! Response: {content[:200]}...")
                else:
                    print(f"✗ No response choices returned")
                    
            except asyncio.TimeoutError:
                print(f"✗ Timeout after 30 seconds")
            except Exception as e:
                print(f"✗ Error: {str(e)[:200]}")
                
    except Exception as e:
        print(f"\nFailed to initialize Databricks client: {e}")
        return False
    
    return True

if __name__ == '__main__':
    result = asyncio.run(test_databricks_llm())
    print(f"\n\nTest {'PASSED' if result else 'FAILED'}")