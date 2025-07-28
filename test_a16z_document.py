#!/usr/bin/env python3
"""Test Vector Search schema with a16z-style document."""

import asyncio
import os
from server.services.ai_engine import AIInsightsEngine
from server.models.schema_models import DEFAULT_VECTOR_SEARCH_SCHEMA

# Load environment
from dotenv import load_dotenv
load_dotenv(".env.local")

async def test_a16z_document():
    """Test Vector Search schema with a16z-style document."""
    
    # Initialize AI engine
    ai_engine = AIInsightsEngine()
    
    # Test document similar to a16z example
    test_doc = """a16z ReRanker Feedback Session
Date: Monday, April 21, 2025 at 1:00:00 PM

Meeting Summary:
a16z discussed their Vector Search implementation and provided feedback on the ReRanker functionality. They are focusing on improving their venture capital research capabilities.

Key Discussion Points:
- Vector Search performance optimization
- ReRanker functionality for investment research
- Real-time query processing for investment analysis
- Internal use by research analysts and investment teams
- RAG implementation for contextual document retrieval
- Similarity matching for finding comparable companies
- Currently in development phase, planning production deployment

Business Context:
a16z operates as a venture capital firm, focusing on technology investments. They need to quickly search and analyze large volumes of investment documents, company information, and market research.

Technical Requirements:
- Real-time search capabilities for analyst queries
- RAG system for contextual information retrieval
- Vector similarity matching for company comparisons
- Internal tool for investment research team
- Development ongoing with production rollout planned

Use Case:
Investment research and due diligence automation to help analysts quickly find relevant information and comparable companies."""

    print("=" * 80)
    print("TESTING A16Z DOCUMENT WITH IMPROVED PROMPTS")
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
    asyncio.run(test_a16z_document())