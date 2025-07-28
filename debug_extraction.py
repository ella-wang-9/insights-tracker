#!/usr/bin/env python3
"""Debug script to test extraction issues."""

import asyncio
import os
from server.services.ai_engine import AIInsightsEngine
from server.models.schema_models import CategoryDefinition, CategoryValueType, SchemaTemplate

# Load environment
from dotenv import load_dotenv
load_dotenv(".env.local")

async def debug_extraction():
    """Debug extraction for specific documents."""
    
    # Initialize AI engine
    ai_engine = AIInsightsEngine()
    
    # Test documents that are having issues
    test_docs = {
        "7-Eleven.docx": """March 11, 2025 | 7-Eleven - Vector Search, Embedding FT

Context
7-Eleven is implementing Vector Search and Embedding FT for their retail operations. They need to analyze customer behavior patterns and optimize inventory management across their stores.

Pain Points
- Manual inventory tracking is inefficient
- Hard to predict customer demand patterns
- Need real-time product recommendations

Use Case
Using Vector Search for product similarity matching and Embedding FT for customer behavior analysis to optimize inventory and improve customer experience.

Usage Pattern
Real-time processing for in-store recommendations and batch analytics for inventory optimization.""",
        
        "a16z.docx": """a16z Meeting Notes

Context
Andreessen Horowitz (a16z) is evaluating our Vector Search and MLflow solutions for their portfolio companies. They're interested in how their startups can use these tools for building AI applications.

Use Cases
- Portfolio company recommendation engine using Vector Search
- MLflow for experiment tracking across portfolio companies
- Building AI agents with tool-calling capabilities

Usage Pattern
They want to run everything in real-time for their investment analysis platform."""
    }
    
    # Define schema with the problematic categories
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
            description="How they plan to use the products (e.g., real-time, batch, streaming)",
            value_type=CategoryValueType.INFERRED
        ),
        CategoryDefinition(
            name="Use Case",
            description="The specific use case or application they want to build",
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
    print("DEBUGGING EXTRACTION ISSUES")
    print("="*80)
    
    for filename, content in test_docs.items():
        print(f"\n{'='*60}")
        print(f"Testing: {filename}")
        print(f"{'='*60}")
        
        try:
            # Enable detailed logging
            print("\nDocument content preview:")
            print(content[:300] + "...")
            
            result = await ai_engine.analyze_text(content, schema, extract_customer_info=True)
            
            print(f"\n--- EXTRACTION RESULTS ---")
            print(f"Customer Name: {result.customer_name or '(EMPTY)'}")
            print(f"Meeting Date: {result.meeting_date or '(EMPTY)'}")
            
            print("\nCategories:")
            for category_name, category_result in result.categories.items():
                values = category_result.values if category_result.values else ["(EMPTY)"]
                print(f"\n{category_name}:")
                print(f"  Values: {', '.join(values)}")
                print(f"  Confidence: {category_result.confidence}")
                print(f"  Model: {category_result.model_used}")
                if category_result.error:
                    print(f"  ERROR: {category_result.error}")
                if category_result.evidence_text and len(category_result.evidence_text) > 0:
                    print(f"  Evidence: {category_result.evidence_text[0][:100]}...")
                    
        except Exception as e:
            print(f"ERROR during extraction: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(debug_extraction())