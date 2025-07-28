#!/usr/bin/env python3
"""Test the AI engine with mock LLM mode."""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.local')

# Enable mock LLM mode
os.environ['USE_MOCK_LLM'] = 'true'

# Import AI engine
from server.models.schema_models import SchemaTemplate, CategoryDefinition, CategoryValueType
from server.services.ai_engine import ai_engine

async def test_ai_engine_mock():
    """Test the AI engine with mock responses."""
    print('Testing AI engine with mock LLM...')

    # Create a simple schema
    schema = SchemaTemplate(
        template_name="test_schema",
        description="Test schema for mock testing",
        categories=[
            CategoryDefinition(
                name="Products",
                description="Products mentioned",
                value_type=CategoryValueType.PREDEFINED,
                possible_values=["Vector Search", "MLflow", "Unity Catalog", "Model Serving"],
                max_values=5
            ),
            CategoryDefinition(
                name="Use Cases",
                description="Customer use cases",
                value_type=CategoryValueType.INFERRED,
                max_values=3
            )
        ]
    )

    test_text = 'Meeting with ACME Corp on January 15th. They need Vector Search for their product catalog.'

    print(f'\nTest text: {test_text}')
    print(f'Schema: {schema.template_name}')
    print(f'Categories: {[cat.name for cat in schema.categories]}')

    try:
        # Test the AI engine analyze_text method
        result = await ai_engine.analyze_text(
            text=test_text, 
            schema=schema, 
            extract_customer_info=True
        )

        print('\nResult:')
        print(f'Customer: {result.customer_name}')
        print(f'Date: {result.meeting_date}')
        print(f'Categories: {len(result.categories)}')

        for category_name, category_result in result.categories.items():
            print(f'\n{category_name}:')
            print(f'  Values: {category_result.values}')
            print(f'  Confidence: {category_result.confidence}')
            print(f'  Model: {category_result.model_used}')
            print(f'  Evidence: {category_result.evidence_text}')

        return True

    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    result = asyncio.run(test_ai_engine_mock())
    print(f'\nTest result: {"SUCCESS" if result else "FAILED"}')
    sys.exit(0 if result else 1)