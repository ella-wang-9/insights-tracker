#!/usr/bin/env python3
"""Test LLM accuracy and performance."""

import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def test_single_document(text, description):
    """Test a single document and measure performance."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"{'='*60}")
    print(f"Document length: {len(text)} characters")
    
    data = {
        "text": text,
        "schema_template_id": "default_product_feedback",
        "extract_customer_info": True
    }
    
    start_time = time.time()
    print("Sending request...")
    
    try:
        response = requests.post(
            f"{API_URL}/insights/analyze-text",
            json=data,
            timeout=180
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ Success in {elapsed:.1f} seconds")
            print(f"\nExtracted Information:")
            print(f"  Customer: {result.get('customer_name', 'N/A')}")
            print(f"  Meeting Date: {result.get('meeting_date', 'N/A')}")
            print(f"  Processing Time (ms): {result.get('processing_time_ms', 'N/A')}")
            
            # Show category details
            categories = result.get('categories', {})
            for cat_name, cat_data in categories.items():
                values = cat_data.get('values', [])
                confidence = cat_data.get('confidence', 0)
                model = cat_data.get('model_used', 'unknown')
                error = cat_data.get('error', None)
                
                print(f"\n  {cat_name}:")
                print(f"    Values: {', '.join(values) if values else 'None'}")
                print(f"    Confidence: {confidence}")
                print(f"    Model: {model}")
                if error:
                    print(f"    Error: {error}")
                    
            return True, elapsed, result
            
        else:
            print(f"\n❌ Failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return False, elapsed, None
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"\n❌ Timeout after {elapsed:.1f} seconds")
        return False, elapsed, None
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ Error after {elapsed:.1f} seconds: {e}")
        return False, elapsed, None

def check_llm_endpoints():
    """Check which LLM endpoints are being used."""
    print("\nChecking LLM endpoint status...")
    
    # Read recent logs
    import subprocess
    try:
        result = subprocess.run(
            ["tail", "-100", "/tmp/databricks-app-watch.log"],
            capture_output=True,
            text=True
        )
        
        logs = result.stdout
        
        # Count endpoint usage
        endpoints = {
            "llama_3_1_70b": logs.count("llama_3_1_70b"),
            "meta_llama_3_70b_instruct-chat": logs.count("meta_llama_3_70b_instruct-chat"),
            "databricks-meta-llama-3-1-8b-instruct": logs.count("databricks-meta-llama-3-1-8b-instruct")
        }
        
        # Count successes and failures
        successes = logs.count("✓ Success with")
        timeouts = logs.count("Timeout after")
        errors = logs.count("Error:")
        
        print(f"\nEndpoint Usage (last 100 log lines):")
        for endpoint, count in endpoints.items():
            print(f"  {endpoint}: {count} attempts")
        
        print(f"\nResults:")
        print(f"  Successes: {successes}")
        print(f"  Timeouts: {timeouts}")
        print(f"  Errors: {errors}")
        
    except Exception as e:
        print(f"Could not read logs: {e}")

def main():
    """Run comprehensive LLM tests."""
    print("="*80)
    print("LLM Performance and Accuracy Test")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # First check endpoint status
    check_llm_endpoints()
    
    # Test documents of varying complexity
    test_cases = [
        # Simple test
        (
            "ACME Corp needs Vector Search.",
            "Minimal document (6 words)"
        ),
        
        # Medium complexity
        (
            "TechCorp meeting on January 15, 2025. They are interested in MLflow for managing their machine learning models. They have over 500 models in production and need better versioning and experiment tracking.",
            "Medium document (32 words)"
        ),
        
        # Complex with multiple products
        (
            """GlobalBank discussion from February 1, 2025.
            
Key topics discussed:
1. Unity Catalog for data governance - They need centralized access control for their data lake
2. Delta Lake for ACID transactions - Critical for their financial reporting
3. MLflow for model management - Planning to deploy 100+ risk models
4. Vector Search for fraud detection - Real-time similarity search on transaction patterns

They are a Fortune 500 financial institution with strict compliance requirements. 
Need to meet SOC2 and PCI compliance standards. Timeline is Q2 2025 for initial deployment.""",
            "Complex document (92 words, multiple products)"
        ),
        
        # Edge case: numbers in company name
        (
            "7-Eleven meeting notes from March 15, 2025. They want to use Vector Search for store location recommendations. Also interested in Embedding FT for personalized offers.",
            "Edge case: number-based company name"
        )
    ]
    
    results = []
    total_time = 0
    
    for text, description in test_cases:
        success, elapsed, result = test_single_document(text, description)
        results.append((description, success, elapsed, result))
        total_time += elapsed
        
        # Add delay between requests to avoid overwhelming the LLM
        if success:
            time.sleep(2)
    
    # Summary
    print("\n" + "="*80)
    print("PERFORMANCE SUMMARY")
    print("="*80)
    
    successful_times = []
    for desc, success, elapsed, result in results:
        status = "✅" if success else "❌"
        print(f"{status} {desc}: {elapsed:.1f}s")
        if success:
            successful_times.append(elapsed)
    
    if successful_times:
        avg_time = sum(successful_times) / len(successful_times)
        print(f"\nAverage successful processing time: {avg_time:.1f} seconds")
        print(f"Min time: {min(successful_times):.1f}s")
        print(f"Max time: {max(successful_times):.1f}s")
    
    print(f"\nTotal test time: {total_time:.1f} seconds")
    
    # Accuracy check
    print("\n" + "="*80)
    print("ACCURACY ANALYSIS")
    print("="*80)
    
    for desc, success, elapsed, result in results:
        if success and result:
            print(f"\n{desc}:")
            
            # Check customer name accuracy
            customer = result.get('customer_name', 'N/A')
            expected_customers = {
                "Minimal document": "ACME Corp",
                "Medium document": "TechCorp",
                "Complex document": "GlobalBank",
                "Edge case": "7-Eleven"
            }
            
            for key, expected in expected_customers.items():
                if key in desc:
                    if customer == expected:
                        print(f"  ✅ Customer name correct: {customer}")
                    else:
                        print(f"  ❌ Customer name incorrect: {customer} (expected: {expected})")
                    break
            
            # Check if products were identified
            categories = result.get('categories', {})
            product_cat = categories.get('Product', {})
            products = product_cat.get('values', [])
            
            if products:
                print(f"  ✅ Products identified: {', '.join(products)}")
            else:
                print(f"  ❌ No products identified")
                
            # Check confidence scores
            avg_confidence = sum(
                cat.get('confidence', 0) 
                for cat in categories.values() 
                if cat.get('values')
            ) / max(1, sum(1 for cat in categories.values() if cat.get('values')))
            
            print(f"  Average confidence: {avg_confidence:.2f}")

if __name__ == "__main__":
    main()