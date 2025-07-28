#!/usr/bin/env python3
"""Debug script to test Databricks Foundation Model integration."""

import asyncio
import os
import sys

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole


async def test_foundation_model():
  """Test the Foundation Model directly."""
  print('Testing Databricks Foundation Model integration...')

  # Load environment
  from dotenv import load_dotenv

  load_dotenv('.env.local')

  print(f'DATABRICKS_HOST: {os.getenv("DATABRICKS_HOST")}')
  print(f'DATABRICKS_TOKEN present: {bool(os.getenv("DATABRICKS_TOKEN"))}')

  try:
    client = WorkspaceClient()
    endpoint_name = 'databricks-meta-llama-3-3-70b-instruct'

    # Test simple query
    test_text = (
      'Meeting with Thermo Fisher on July 9, 2025. They discussed implementing vector search.'
    )

    prompt = f"""Analyze this customer meeting text and identify products mentioned.

Customer meeting notes text:
"{test_text}"

Possible products: Vector Search, Real-time Search, Keyword Search, Batch Processing

You MUST respond with ONLY a JSON object:
{{"values": ["product1"], "evidence": ["text snippet"], "confidence": 0.8}}"""

    print(f'\nSending prompt ({len(prompt)} chars):')
    print(prompt)
    print('\n' + '=' * 50)

    messages = [ChatMessage(role=ChatMessageRole.USER, content=prompt)]

    response = client.serving_endpoints.query(
      name=endpoint_name, messages=messages, max_tokens=200, temperature=0.1
    )

    if response.choices and len(response.choices) > 0:
      content = response.choices[0].message.content
      print('Foundation Model Response:')
      print(content)
      print('\n' + '=' * 50)

      # Test JSON extraction
      import json
      import re

      json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
      if json_match:
        json_text = json_match.group()
        print(f'Extracted JSON: {json_text}')
        try:
          parsed = json.loads(json_text)
          print(f'Successfully parsed: {parsed}')
          return True
        except json.JSONDecodeError as e:
          print(f'JSON parse error: {e}')
          return False
      else:
        print('No JSON found in response')
        return False
    else:
      print('No response choices')
      return False

  except Exception as e:
    print(f'Error: {e}')
    import traceback

    traceback.print_exc()
    return False


if __name__ == '__main__':
  result = asyncio.run(test_foundation_model())
  sys.exit(0 if result else 1)
