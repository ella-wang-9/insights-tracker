#!/usr/bin/env python3
"""Test script to debug empty field extraction issues."""

import asyncio
import os
from server.services.ai_engine import AIInsightsEngine
from server.models.schema_models import CategoryDefinition, CategoryValueType, SchemaTemplate

# Load environment
from dotenv import load_dotenv
load_dotenv(".env.local")

async def test_empty_fields():
    """Test extraction with documents that have been returning empty fields."""
    
    # Initialize AI engine
    ai_engine = AIInsightsEngine()
    
    # Test document that should have all fields
    test_doc = """
    ActiveFence Meeting Notes
    Date: March 04, 2025
    
    ActiveFence is a trust and safety platform that needs our Vector Search and Embedding FT 
    solutions for content moderation. They also want to use Delta Lake for data management.
    
    Industry: Trust & Safety / Content Moderation
    
    Use Case: They want to build a real-time content moderation system that can:
    - Detect harmful content across multiple platforms
    - Identify emerging threats and patterns
    - Scale to millions of posts per day
    
    Usage Pattern: Real-time processing with batch analytics
    
    Products discussed:
    - Vector Search for similarity matching
    - Embedding FT for content understanding  
    - Delta Lake for data storage
    """
    
    # Define schema with all category types
    categories = [
        CategoryDefinition(
            name="Customer Name",
            description="The name of the customer or company",
            value_type=CategoryValueType.INFERRED
        ),
        CategoryDefinition(
            name="Meeting Date", 
            description="The date of the meeting",
            value_type=CategoryValueType.INFERRED
        ),
        CategoryDefinition(
            name="Product",
            description="Databricks products mentioned",
            value_type=CategoryValueType.PREDEFINED,
            possible_values=["Vector Search", "Embedding FT", "MLflow", "Delta Lake", "Model Serving"]
        ),
        CategoryDefinition(
            name="Industry",
            description="The industry or business sector",
            value_type=CategoryValueType.INFERRED
        ),
        CategoryDefinition(
            name="Usage Pattern",
            description="How they plan to use the products",
            value_type=CategoryValueType.INFERRED
        ),
        CategoryDefinition(
            name="Use Case",
            description="The specific use case or application",
            value_type=CategoryValueType.INFERRED
        )
    ]
    
    schema = SchemaTemplate(
        template_id="test_schema",
        template_name="Test Schema",
        categories=categories,
        is_default=False
    )
    
    print("="*80)
    print("Testing extraction with comprehensive document")
    print("="*80)
    print(f"Document preview: {test_doc[:200]}...")
    print()
    
    # Run extraction
    try:
        result = await ai_engine.analyze_text(test_doc, schema, extract_customer_info=True)
        
        print("\n" + "="*80)
        print("EXTRACTION RESULTS")
        print("="*80)
        
        # Check customer info
        print(f"\nCustomer Name: {result.customer_name or '(EMPTY)'}")
        print(f"Meeting Date: {result.meeting_date or '(EMPTY)'}")
        
        # Check each category
        print("\nCategories:")
        for category_name, category_result in result.categories.items():
            values = category_result.values if category_result.values else ["(EMPTY)"]
            print(f"\n{category_name}:")
            print(f"  Values: {', '.join(values)}")
            print(f"  Confidence: {category_result.confidence}")
            print(f"  Model: {category_result.model_used}")
            if category_result.error:
                print(f"  ERROR: {category_result.error}")
            if category_result.evidence_text:
                print(f"  Evidence: {category_result.evidence_text[0][:100]}...")
        
        # Summary of empty fields
        print("\n" + "="*80)
        print("EMPTY FIELDS SUMMARY")
        print("="*80)
        
        empty_fields = []
        if not result.customer_name:
            empty_fields.append("Customer Name")
        if not result.meeting_date:
            empty_fields.append("Meeting Date")
            
        for category_name, category_result in result.categories.items():
            if not category_result.values or len(category_result.values) == 0:
                empty_fields.append(category_name)
        
        if empty_fields:
            print(f"Empty fields found: {', '.join(empty_fields)}")
            print("\nDebugging suggestions:")
            print("1. Check server logs for LLM response details")
            print("2. Verify LLM endpoints are responding")
            print("3. Check for rate limiting issues")
            print("4. Review prompt formatting")
        else:
            print("✅ All fields extracted successfully!")
            
    except Exception as e:
        print(f"\nERROR during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_empty_fields())