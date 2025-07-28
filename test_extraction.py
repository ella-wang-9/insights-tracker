#!/usr/bin/env python3
import asyncio
import os
from server.services.ai_engine import AIInsightsEngine
from server.models.schema_models import CategoryDefinition, CategoryValueType

# Load environment
from dotenv import load_dotenv
load_dotenv(".env.local")

async def test_extraction():
    # Initialize AI engine
    ai_engine = AIInsightsEngine()
    
    # Test documents
    test_docs = {
        "7-Eleven.docx": """March 11, 2025 | 7-Eleven - Vector Search, Embedding FT

Context
7-Eleven is implementing Vector Search and Embedding FT for their retail operations. They need to analyze customer behavior patterns and optimize inventory management across their stores.

Pain Points
- Manual inventory tracking is inefficient
- Hard to predict customer demand patterns
- Need real-time product recommendations

Use Case
Using Vector Search for product similarity matching and Embedding FT for customer behavior analysis to optimize inventory and improve customer experience.""",
        
        "a16z.docx": """a16z Meeting Notes

Context
Andreessen Horowitz (a16z) is evaluating our Vector Search and MLflow solutions for their portfolio companies. They're interested in how their startups can use these tools for building AI applications.

Use Cases
- Portfolio company recommendation engine using Vector Search
- MLflow for experiment tracking across portfolio companies
- Building AI agents with tool-calling capabilities

They want to run everything in real-time for their investment analysis platform.""",
        
        "Adlumin.docx": """Nov 12, 2024 | Adlumin - Vector Search

Context
Adlumin is a cybersecurity company that provides managed detection and response (MDR) services. They want to use Vector Search to analyze security logs and detect anomalies in real-time.

Pain Points
- Current log analysis is slow and manual
- Hard to detect patterns across millions of events
- Need real-time threat detection

Use Case
Security log analysis and anomaly detection using Vector Search for real-time threat identification."""
    }
    
    # Test with default schema categories
    categories = [
        CategoryDefinition(
            name="Customer Name",
            description="The name of the customer or company",
            value_type=CategoryValueType.INFERRED
        ),
        CategoryDefinition(
            name="Meeting Date",
            description="The date of the meeting or engagement",
            value_type=CategoryValueType.INFERRED
        ),
        CategoryDefinition(
            name="Product",
            description="The Databricks products mentioned",
            value_type=CategoryValueType.PREDEFINED,
            possible_values=["Vector Search", "Embedding FT", "MLflow", "Delta Lake", "Model Serving"]
        ),
        CategoryDefinition(
            name="Industry",
            description="The industry or sector of the customer",
            value_type=CategoryValueType.INFERRED
        ),
        CategoryDefinition(
            name="Usage Pattern",
            description="How the customer uses or plans to use the product",
            value_type=CategoryValueType.INFERRED
        ),
        CategoryDefinition(
            name="Use Case",
            description="The specific use case or application",
            value_type=CategoryValueType.INFERRED
        )
    ]
    
    print("Testing document extraction with improved AI engine...\n")
    
    for filename, content in test_docs.items():
        print(f"\n{'='*60}")
        print(f"Testing: {filename}")
        print(f"{'='*60}")
        
        try:
            result = await ai_engine.extract_from_text(content, categories)
            
            print("\nExtracted results:")
            for category_name, value in result.items():
                print(f"  {category_name}: {value if value else '(empty)'}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n\nTesting custom schema with description...")
    
    # Test with custom schema
    custom_categories = [
        CategoryDefinition(
            name="Company",
            description="The organization or business entity being discussed",
            value_type=CategoryValueType.INFERRED
        ),
        CategoryDefinition(
            name="Technology Stack",
            description="The specific technologies, tools, or platforms mentioned",
            value_type=CategoryValueType.INFERRED
        ),
        CategoryDefinition(
            name="Business Challenge",
            description="The main problems or pain points the company is trying to solve",
            value_type=CategoryValueType.INFERRED
        ),
        CategoryDefinition(
            name="Implementation Timeline",
            description="Any dates, deadlines, or time-related information",
            value_type=CategoryValueType.INFERRED
        )
    ]
    
    print(f"\n{'='*60}")
    print(f"Testing custom schema on: a16z.docx")
    print(f"{'='*60}")
    
    try:
        result = await ai_engine.extract_from_text(test_docs["a16z.docx"], custom_categories)
        
        print("\nExtracted results with custom schema:")
        for category_name, value in result.items():
            print(f"  {category_name}: {value if value else '(empty)'}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_extraction())