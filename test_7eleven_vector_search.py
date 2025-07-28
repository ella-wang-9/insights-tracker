#!/usr/bin/env python3
"""Test Vector Search schema with 7-Eleven document."""

import asyncio
import os
from server.services.ai_engine import AIInsightsEngine
from server.models.schema_models import DEFAULT_VECTOR_SEARCH_SCHEMA

# Load environment
from dotenv import load_dotenv
load_dotenv(".env.local")

async def test_7eleven_vector_search():
    """Test Vector Search schema with 7-Eleven document."""
    
    # Initialize AI engine
    ai_engine = AIInsightsEngine()
    
    # Test document similar to 7-Eleven
    test_doc = """7-Eleven - Vector Search Implementation
Date: March 11, 2025

Meeting Summary:
7-Eleven discussed implementing Vector Search and Embedding Fine Tuning for their retail operations. They need real-time recommendations for customers and batch processing for inventory.

Key Points:
- Vector Search for product recommendations
- Real-time customer recommendations in stores  
- Batch processing for inventory analysis
- RAG system for contextual suggestions
- Internal use by store operations team
- Pilot phase before production rollout

Business Context:
7-Eleven is a retail convenience store chain needing to improve customer experience through personalized recommendations and optimize inventory management.

Technical Approach:
- Vector Search for similarity matching
- RAG implementation for product suggestions
- Real-time processing during shopping
- Document processing for inventory data
- Internal tool for store managers
- Currently in POC/pilot phase"""

    print("=" * 80)
    print("TESTING 7-ELEVEN WITH VECTOR SEARCH SCHEMA")
    print("=" * 80)
    print(f"Document length: {len(test_doc)} chars")
    print()
    
    try:
        result = await ai_engine.analyze_text(
            test_doc, 
            DEFAULT_VECTOR_SEARCH_SCHEMA, 
            extract_customer_info=True
        )
        
        print("--- EXTRACTION RESULTS ---")
        print(f"Customer Name: {result.customer_name or '(EMPTY)'}")
        print(f"Meeting Date: {result.meeting_date or '(EMPTY)'}")
        
        # Check each category
        expected_categories = [
            "Product", "Industry", "Usage Pattern", "Search Tags", 
            "Unstructured Tags", "End User Tags", "Production Status"
        ]
        
        print("\nVector Search Schema Categories:")
        empty_fields = []
        
        for category_name in expected_categories:
            if category_name in result.categories:
                category_result = result.categories[category_name]
                values = category_result.values if category_result.values else ["(EMPTY)"]
                if not category_result.values:
                    empty_fields.append(category_name)
                    values = ["-"]
                print(f"{category_name}: {', '.join(values)}")
            else:
                print(f"{category_name}: NOT FOUND")
                empty_fields.append(category_name)
        
        print(f"\nSUMMARY:")
        if empty_fields:
            print(f"⚠️  EMPTY FIELDS ({len(empty_fields)}/7): {', '.join(empty_fields)}")
        else:
            print(f"✅ ALL FIELDS EXTRACTED SUCCESSFULLY")
            
    except Exception as e:
        print(f"\nERROR during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_7eleven_vector_search())