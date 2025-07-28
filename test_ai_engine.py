#!/usr/bin/env python3
"""Test the AI engine directly to debug the issue."""

import asyncio
import sys

from dotenv import load_dotenv

# Load environment
load_dotenv('.env.local')

# Import AI engine
from server.routers.schema import _schemas
from server.services.ai_engine import ai_engine


async def test_ai_engine():
  """Test the AI engine directly."""
  print('Testing AI engine...')

  # Get default schema
  schema = _schemas.get('default_product_feedback')
  if not schema:
    print('No default schema found')
    return False

  test_text = 'Meeting with Thermo Fisher on July 9, 2025. They discussed implementing vector search for their pharmaceutical data platform. Currently using basic keyword search but want semantic capabilities for batch processing of drug research documents.'

  print(f'Test text: {test_text}')
  print(f'Schema: {schema.template_name}')
  print(f'Categories: {[cat.name for cat in schema.categories]}')

  try:
    # Test the AI engine analyze_text method
    result = await ai_engine.analyze_text(text=test_text, schema=schema, extract_customer_info=True)

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

    # Check if any categories used the Foundation Model
    foundation_model_used = any(
      cat.model_used == 'databricks-meta-llama-3-3-70b-instruct'
      for cat in result.categories.values()
    )

    print(f'\nFoundation Model used: {foundation_model_used}')
    return foundation_model_used

  except Exception as e:
    print(f'Error: {e}')
    import traceback

    traceback.print_exc()
    return False


if __name__ == '__main__':
  result = asyncio.run(test_ai_engine())
  print(f'\nTest result: {"SUCCESS" if result else "FAILED"}')
  sys.exit(0 if result else 1)
