#!/usr/bin/env python3
"""Simple test to verify Vector Search schema exists."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test import directly
try:
    from server.models.schema_models import DEFAULT_VECTOR_SEARCH_SCHEMA, DEFAULT_PRODUCT_FEEDBACK_SCHEMA
    
    print("=== SCHEMA IMPORT TEST ===")
    print("✅ Successfully imported both schemas")
    
    print(f"\n=== PRODUCT FEEDBACK SCHEMA ===")
    print(f"Name: {DEFAULT_PRODUCT_FEEDBACK_SCHEMA.template_name}")
    print(f"ID: {DEFAULT_PRODUCT_FEEDBACK_SCHEMA.template_id}")
    print(f"Categories: {[cat.name for cat in DEFAULT_PRODUCT_FEEDBACK_SCHEMA.categories]}")
    
    print(f"\n=== VECTOR SEARCH SCHEMA ===")
    print(f"Name: {DEFAULT_VECTOR_SEARCH_SCHEMA.template_name}")
    print(f"ID: {DEFAULT_VECTOR_SEARCH_SCHEMA.template_id}")
    print(f"Categories: {[cat.name for cat in DEFAULT_VECTOR_SEARCH_SCHEMA.categories]}")
    
    print(f"\n✅ Both schemas are properly defined!")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"❌ Error: {e}")