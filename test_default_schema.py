#!/usr/bin/env python3
"""Test default schema extraction with improved prompts."""

import asyncio
import os
from server.services.ai_engine import AIInsightsEngine
from server.models.schema_models import DEFAULT_PRODUCT_FEEDBACK_SCHEMA

# Load environment
from dotenv import load_dotenv
load_dotenv(".env.local")

async def test_default_schema():
    """Test default schema extraction with improved prompts."""
    
    # Initialize AI engine
    ai_engine = AIInsightsEngine()
    
    # Test documents that cover all categories
    test_docs = {
        "7-Eleven_comprehensive.docx": """March 11, 2025 | 7-Eleven - Vector Search and Embedding FT Implementation

Company Overview:
7-Eleven is a major retail convenience store chain implementing Vector Search and Embedding FT for their operations. 

Business Context:
As a retail company, 7-Eleven needs to analyze customer behavior patterns and optimize inventory management across their 70,000+ stores worldwide.

Pain Points:
- Manual inventory tracking is inefficient  
- Hard to predict customer demand patterns
- Need real-time product recommendations for customers
- Want to improve customer experience through personalization

Proposed Solution:
Using Vector Search for product similarity matching and Embedding FT for customer behavior analysis. They also want MLflow for experiment tracking of their recommendation models.

Use Case:
Product Recommendations - They want to build a recommendation engine that suggests relevant products to customers based on purchase history and current selections.

Implementation Approach:
The system will run real-time processing for in-store recommendations when customers are shopping, plus batch analytics overnight for inventory optimization. They want immediate recommendations on their mobile app and in-store kiosks.

Technical Requirements:
- Real-time recommendations during shopping
- Batch processing for overnight inventory analysis  
- Vector Search for finding similar products
- Embedding FT for understanding customer preferences
- MLflow for tracking recommendation model performance""",
        
        "ActiveFence_security.docx": """ActiveFence - Content Moderation Platform
Date: March 04, 2025

Company Profile:
ActiveFence is a cybersecurity and trust & safety company that provides content moderation solutions.

Industry Context:
As a technology company in the cybersecurity space, ActiveFence helps social media platforms and online services detect harmful content.

Business Challenge:
They need to process millions of posts per day to identify harmful content, detect emerging threats, and protect users from abuse and misinformation.

Solution Requirements:
Looking to implement Vector Search and Delta Lake for their content analysis pipeline. They need batch processing capabilities to analyze large volumes of content overnight, plus interactive search for investigators to explore specific cases.

Primary Use Case:
Anomaly Detection - Identifying unusual patterns in content that might indicate coordinated attacks, spam campaigns, or emerging threats.

Technical Implementation:
- Batch processing for analyzing daily content volumes
- Interactive queries for security analysts to investigate specific cases  
- Vector Search for finding similar harmful content patterns
- Delta Lake for storing and managing large content datasets

Processing Pattern:
Primarily batch processing with some interactive analysis capabilities for deep-dive investigations."""
    }
    
    print("="*80)
    print("TESTING DEFAULT SCHEMA WITH IMPROVED PROMPTS")
    print("="*80)
    print(f"Schema: {DEFAULT_PRODUCT_FEEDBACK_SCHEMA.template_name}")
    print(f"Categories: {[cat.name for cat in DEFAULT_PRODUCT_FEEDBACK_SCHEMA.categories]}")
    print()
    
    for filename, content in test_docs.items():
        print(f"\n{'='*60}")
        print(f"Testing: {filename}")
        print(f"{'='*60}")
        print(f"Document length: {len(content)} chars")
        
        try:
            result = await ai_engine.analyze_text(
                content, 
                DEFAULT_PRODUCT_FEEDBACK_SCHEMA, 
                extract_customer_info=True
            )
            
            print(f"\n--- EXTRACTION RESULTS ---")
            print(f"Customer Name: {result.customer_name or '(EMPTY)'}")
            print(f"Meeting Date: {result.meeting_date or '(EMPTY)'}")
            
            # Check each default schema category
            expected_categories = ["Product", "Industry", "Usage Pattern", "Use Case"]
            print(f"\nDefault Schema Categories:")
            
            for category_name in expected_categories:
                if category_name in result.categories:
                    category_result = result.categories[category_name]
                    values = category_result.values if category_result.values else ["(EMPTY)"]
                    print(f"\n{category_name}:")
                    print(f"  Values: {', '.join(values)}")
                    print(f"  Confidence: {category_result.confidence}")
                    print(f"  Model: {category_result.model_used}")
                    if category_result.error:
                        print(f"  ERROR: {category_result.error}")
                    if category_result.evidence_text and len(category_result.evidence_text) > 0:
                        print(f"  Evidence: {category_result.evidence_text[0][:150]}...")
                else:
                    print(f"\n{category_name}: NOT FOUND")
            
            # Check for any empty fields
            empty_fields = []
            if not result.customer_name:
                empty_fields.append("Customer Name")
            if not result.meeting_date:
                empty_fields.append("Meeting Date")
                
            for category_name in expected_categories:
                if category_name in result.categories:
                    if not result.categories[category_name].values:
                        empty_fields.append(category_name)
                else:
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
    asyncio.run(test_default_schema())