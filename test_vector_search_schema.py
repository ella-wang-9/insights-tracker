#!/usr/bin/env python3
"""Test Vector Search schema extraction."""

import asyncio
import os
from server.services.ai_engine import AIInsightsEngine
from server.models.schema_models import DEFAULT_VECTOR_SEARCH_SCHEMA

# Load environment
from dotenv import load_dotenv
load_dotenv(".env.local")

async def test_vector_search_schema():
    """Test Vector Search schema extraction."""
    
    # Initialize AI engine
    ai_engine = AIInsightsEngine()
    
    # Test document based on the examples provided
    test_doc = """7-Eleven - Vector Search Implementation Discussion
Date: Tuesday, March 11, 2025 at 1:00:00 PM

Meeting Summary:
7-Eleven discussed implementing Vector Search and Embedding Fine Tuning for their retail operations. They need both real-time recommendations for customers shopping in stores and batch processing for overnight inventory analysis.

Key Discussion Points:
- Vector Search for product similarity matching
- Embedding FT for customer behavior analysis  
- RAG (Retrieval Augmented Generation) capabilities for personalized recommendations
- Real-time processing during shopping hours
- Batch analytics overnight for inventory optimization
- Internal use by store operations team
- Solution will be deployed to production after pilot

Search Capabilities:
- RAG implementation for contextual recommendations
- Similarity matching for product suggestions
- Search functionality for inventory lookup

Unstructured Data Processing:
- RAG processing of product descriptions
- Automation of recommendation workflows
- Document processing for inventory management

Industry Context:
7-Eleven operates in the retail/convenience store space with 70,000+ locations globally.

Technical Implementation:
- RAG system for product recommendations
- Real-time matching during customer interactions
- Automation of inventory suggestions
- Production deployment planned after successful pilot"""

    print("=" * 80)
    print("TESTING VECTOR SEARCH SCHEMA")
    print("=" * 80)
    print(f"Schema: {DEFAULT_VECTOR_SEARCH_SCHEMA.template_name}")
    print(f"Categories: {[cat.name for cat in DEFAULT_VECTOR_SEARCH_SCHEMA.categories]}")
    print()
    
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
                print(f"\n{category_name}:")
                print(f"  Values: {', '.join(values)}")
                print(f"  Confidence: {category_result.confidence}")
                if category_result.evidence_text and len(category_result.evidence_text) > 0:
                    print(f"  Evidence: {category_result.evidence_text[0][:100]}...")
                
                if not category_result.values:
                    empty_fields.append(category_name)
            else:
                print(f"\n{category_name}: NOT FOUND")
                empty_fields.append(category_name)
        
        if empty_fields:
            print(f"\n⚠️  EMPTY FIELDS: {', '.join(empty_fields)}")
        else:
            print(f"\n✅ ALL FIELDS EXTRACTED SUCCESSFULLY")
            
    except Exception as e:
        print(f"\nERROR during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_vector_search_schema())