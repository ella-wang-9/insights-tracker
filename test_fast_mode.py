#!/usr/bin/env python3
"""Test script to verify fast mode functionality."""

import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

from server.models.schema_models import DEFAULT_PRODUCT_FEEDBACK_SCHEMA
from server.services.ai_engine import ai_engine


async def test_fast_mode():
  """Test that fast mode bypasses AI calls and returns results quickly."""
  print('🧪 Testing Fast Mode Implementation')
  print('=' * 50)

  # Test text with clear patterns
  test_text = """
    Meeting with Acme Corp on March 15, 2024
    
    They are looking for a vector search solution for their e-commerce platform.
    Currently using keyword search but need semantic capabilities.
    Timeline is urgent - need to go live by Q2.
    """

  schema = DEFAULT_PRODUCT_FEEDBACK_SCHEMA

  print(f'📄 Test Text: {test_text[:100]}...')
  print(f'📋 Schema: {schema.template_name}')
  print(f'📊 Categories: {len(schema.categories)}')

  print('\n🚀 Testing Fast Mode (should be very fast)...')
  import time

  start_time = time.time()

  try:
    result = await ai_engine.analyze_text(
      text=test_text, schema=schema, extract_customer_info=True, fast_mode=True
    )

    end_time = time.time()
    duration = end_time - start_time

    print(f'✅ Fast mode completed in {duration:.2f} seconds')
    print(f'👤 Customer Name: {result.customer_name}')
    print(f'📅 Meeting Date: {result.meeting_date}')
    print(f'📈 Processing Time: {result.processing_time_ms}ms')
    print(f'📝 Word Count: {result.word_count}')

    print('\n📋 Category Results:')
    for category_name, category_result in result.categories.items():
      print(
        f'  • {category_name}: {category_result.values} (confidence: {category_result.confidence:.2f})'
      )
      print(f'    Model used: {category_result.model_used}')

    # Verify no AI models were used
    models_used = [cat.model_used for cat in result.categories.values()]
    ai_models_used = [m for m in models_used if 'fallback' not in m and 'keyword' not in m]

    if ai_models_used:
      print(f'❌ FAIL: AI models were still used in fast mode: {ai_models_used}')
      return False
    else:
      print('✅ SUCCESS: Fast mode used only fallback methods, no AI calls')
      return True

  except Exception as e:
    print(f'❌ ERROR: Fast mode test failed: {e}')
    import traceback

    traceback.print_exc()
    return False


async def test_customer_extraction_fallback():
  """Test the customer info extraction fallback method directly."""
  print('\n🧪 Testing Customer Info Fallback')
  print('=' * 50)

  test_texts = [
    'Meeting with Acme Corp on March 15, 2024',
    'Call with Tesla Inc on 12/31/2023',
    'Discussion with Microsoft team on January 5, 2024',
    'Random text without clear customer info',
  ]

  for i, text in enumerate(test_texts, 1):
    print(f"\n{i}. Testing: '{text}'")
    try:
      customer, date = await ai_engine._extract_customer_info_fallback(text)
      print(f'   Customer: {customer}')
      print(f'   Date: {date}')
    except Exception as e:
      print(f'   ERROR: {e}')


if __name__ == '__main__':
  print('🔧 Testing Fast Mode Implementation')
  print('This script verifies that fast mode works correctly and bypasses AI calls')

  async def main():
    success1 = await test_fast_mode()
    await test_customer_extraction_fallback()

    if success1:
      print('\n🎉 All tests passed! Fast mode is working correctly.')
    else:
      print('\n❌ Some tests failed. Check the implementation.')

  asyncio.run(main())
