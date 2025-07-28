#!/usr/bin/env python3
"""Test script to verify deployed Databricks app functionality."""

import os
import requests
import json
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.local')

DATABRICKS_HOST = os.getenv('DATABRICKS_HOST')
DATABRICKS_TOKEN = os.getenv('DATABRICKS_TOKEN')
APP_NAME = 'customer-insights-v2'

# Construct app URL
APP_URL = f"{DATABRICKS_HOST}/apps/{APP_NAME}"
API_URL = f"{APP_URL}/api"

# Headers for authentication
headers = {
    'Authorization': f'Bearer {DATABRICKS_TOKEN}',
    'Content-Type': 'application/json'
}

def test_app_health():
    """Test if the app is responding."""
    print(f"Testing app at: {APP_URL}")
    
    try:
        # Test root endpoint
        response = requests.get(APP_URL, headers=headers, timeout=30)
        print(f"App root status: {response.status_code}")
        
        # Test API docs
        response = requests.get(f"{API_URL}/docs", headers=headers, timeout=30)
        print(f"API docs status: {response.status_code}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error accessing app: {e}")
        return False

def test_schema_endpoints():
    """Test schema management endpoints."""
    print("\nTesting schema endpoints...")
    
    try:
        # Get schema templates
        response = requests.get(f"{API_URL}/schema/templates", headers=headers, timeout=30)
        print(f"Schema templates status: {response.status_code}")
        
        if response.status_code == 200:
            templates = response.json()
            print(f"Found {len(templates)} schema templates")
            if templates:
                print(f"First template: {templates[0]['template_name']}")
            return True
    except Exception as e:
        print(f"Error testing schemas: {e}")
    
    return False

def test_text_analysis():
    """Test text analysis endpoint."""
    print("\nTesting text analysis...")
    
    test_data = {
        "text": "ACME Corp needs Vector Search for their product catalog.",
        "schema_template_id": "default_product_feedback",
        "extract_customer_info": True
    }
    
    try:
        response = requests.post(
            f"{API_URL}/insights/analyze-text",
            headers=headers,
            json=test_data,
            timeout=60
        )
        
        print(f"Text analysis status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Customer extracted: {result.get('customer_name')}")
            print(f"Categories processed: {len(result.get('categories', {}))}")
            return True
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing text analysis: {e}")
    
    return False

def test_batch_processing():
    """Test batch processing capabilities."""
    print("\nTesting batch processing...")
    
    # Create test file
    test_file = Path("/tmp/test_doc.txt")
    test_file.write_text("TechCorp meeting on Jan 15, 2025. They need MLflow for model management.")
    
    try:
        with open(test_file, 'rb') as f:
            files = {'files': ('test_doc.txt', f, 'text/plain')}
            data = {
                'schema_template_id': 'default_product_feedback',
                'extract_customer_info': 'true',
                'export_format': 'xlsx'
            }
            
            response = requests.post(
                f"{API_URL}/batch/analyze-files-with-preview",
                headers={'Authorization': f'Bearer {DATABRICKS_TOKEN}'},
                files=files,
                data=data,
                timeout=120
            )
        
        print(f"Batch processing status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Processed files: {len(result.get('table_data', []))}")
            return True
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error testing batch processing: {e}")
    finally:
        test_file.unlink(missing_ok=True)
    
    return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Databricks App Deployment Test")
    print("=" * 60)
    
    tests = [
        ("App Health", test_app_health),
        ("Schema Endpoints", test_schema_endpoints),
        ("Text Analysis", test_text_analysis),
        ("Batch Processing", test_batch_processing)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        success = test_func()
        results.append((test_name, success))
        print(f"Result: {'✅ PASS' if success else '❌ FAIL'}")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    for test_name, success in results:
        print(f"{test_name}: {'✅ PASS' if success else '❌ FAIL'}")
    
    total_passed = sum(1 for _, success in results if success)
    print(f"\nTotal: {total_passed}/{len(tests)} tests passed")
    
    if total_passed == len(tests):
        print("\n🎉 All tests passed! The app is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the deployment logs.")

if __name__ == "__main__":
    main()