#!/usr/bin/env python3
"""Test if Vector Search schema is available in the API."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server.routers.schema import _schemas

def test_schemas():
    """Test available schemas."""
    print("=== AVAILABLE SCHEMAS ===")
    print(f"Total schemas: {len(_schemas)}")
    
    for schema_id, schema in _schemas.items():
        print(f"\nSchema ID: {schema_id}")
        print(f"Name: {schema.template_name}")
        print(f"Is Default: {schema.is_default}")
        print(f"Categories: {[cat.name for cat in schema.categories]}")
    
    # Test API endpoint
    import asyncio
    from server.routers.schema import get_schema_templates
    
    print("\n=== API RESPONSE ===")
    
    async def test_api():
        templates = await get_schema_templates()
        print(f"API returned {len(templates)} templates:")
        for template in templates:
            print(f"  - {template.template_name} ({template.template_id})")
    
    asyncio.run(test_api())

if __name__ == "__main__":
    test_schemas()