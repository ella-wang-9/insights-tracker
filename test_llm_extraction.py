#!/usr/bin/env python3
"""Test LLM extraction directly."""

import asyncio
import os
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

# Load environment
from dotenv import load_dotenv
load_dotenv(".env.local")

async def test_llm_directly():
    """Test LLM extraction with specific prompts."""
    
    # Initialize Databricks client
    w = WorkspaceClient(
        host=os.getenv("DATABRICKS_HOST"),
        token=os.getenv("DATABRICKS_TOKEN")
    )
    
    # Test document content
    test_doc = """March 11, 2025 | 7-Eleven - Vector Search, Embedding FT

Context
7-Eleven is implementing Vector Search and Embedding FT for their retail operations. They need to analyze customer behavior patterns and optimize inventory management across their stores.

Pain Points
- Manual inventory tracking is inefficient
- Hard to predict customer demand patterns
- Need real-time product recommendations

Use Case
Using Vector Search for product similarity matching and Embedding FT for customer behavior analysis to optimize inventory and improve customer experience.

Usage Pattern
Real-time processing for in-store recommendations and batch analytics for inventory optimization."""

    # Test customer extraction with simplified prompt
    customer_prompt = f"""Extract the customer name and meeting date from this text.

Text: {test_doc}

Return a JSON object with these fields:
- customer_name: The company or customer name (e.g., "7-Eleven", "a16z", "ActiveFence")
- meeting_date: The date in format "MMM DD, YYYY" (e.g., "Mar 11, 2025")

If a field is not found, use empty string "".

Example: {{"customer_name": "7-Eleven", "meeting_date": "Mar 11, 2025"}}"""
    
    # Test usage pattern extraction
    usage_pattern_prompt = f"""Extract values for the category "Usage Pattern" from the text.

CATEGORY: Usage Pattern
DESCRIPTION: How they plan to use the products (e.g., real-time, batch, streaming)

This category is asking about patterns, types, or modes of usage.
Extract how something is used, patterns of behavior, or types of implementation.

TEXT TO ANALYZE:
"{test_doc}"

INSTRUCTIONS:
1. For "Usage Pattern", extract ALL relevant values from the text
2. Be specific and concise (1-4 words per value)
3. Focus on what the text actually says about Usage Pattern
4. If no relevant information is found, return empty values
5. Provide evidence from the text to support your extraction
6. Look through the ENTIRE document, not just the beginning
7. Be thorough - extract ALL mentions, not just the first one

Return ONLY JSON: {{"values": ["relevant_value"], "evidence": ["supporting text"], "confidence": 0.9}}"""

    # Test prompts
    prompts = [
        ("Customer Extraction", customer_prompt),
        ("Usage Pattern Extraction", usage_pattern_prompt)
    ]
    
    endpoint = "databricks-gemini-2-5-flash"
    
    for prompt_name, prompt in prompts:
        print(f"\n{'='*60}")
        print(f"Testing: {prompt_name}")
        print(f"{'='*60}")
        print(f"Prompt length: {len(prompt)} chars")
        
        try:
            # Create message
            messages = [ChatMessage(role=ChatMessageRole.USER, content=prompt)]
            
            # Query model
            print(f"Querying {endpoint}...")
            response = w.serving_endpoints.query(
                name=endpoint,
                messages=messages,
                max_tokens=500,
                temperature=0.1
            )
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                print(f"\nResponse length: {len(content)} chars")
                print(f"Full response:\n{content}")
            else:
                print("No response received")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm_directly())