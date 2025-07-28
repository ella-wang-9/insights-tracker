#!/usr/bin/env python3
"""Test the new column selection feature."""

import requests
import json

def test_column_selection():
    """Test the available columns endpoint and column selection."""
    
    base_url = "https://customer-insights-v2-6051921418418893.staging.aws.databricksapps.com"
    
    print("=== Testing Column Selection Feature ===")
    
    # Test 1: Get available columns for Vector Search schema
    print("\n1. Testing available columns endpoint...")
    schema_id = "default_vector_search"
    
    try:
        response = requests.get(f"{base_url}/api/batch/available-columns/{schema_id}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            columns_data = response.json()
            print("✅ Available columns endpoint working!")
            print(f"Base columns: {columns_data['base_columns']}")
            print(f"Category columns: {columns_data['category_columns']}")
            print(f"Total columns: {len(columns_data['all_columns'])}")
            
            # Expected Vector Search columns
            expected_categories = ["Product", "Industry", "Usage Pattern", "Search Tags", "Unstructured Tags", "End User Tags", "Production Status"]
            
            print("\n2. Verifying column formatting...")
            for category in expected_categories:
                if category in columns_data['category_columns']:
                    print(f"✅ {category} - properly formatted with spaces and capitalization")
                else:
                    print(f"❌ {category} - not found in available columns")
                    
        else:
            print(f"❌ Failed to get columns: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing columns endpoint: {e}")

if __name__ == "__main__":
    test_column_selection()