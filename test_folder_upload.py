#!/usr/bin/env python3
"""Test script to verify folder upload functionality."""

import requests
import json
import base64
from pathlib import Path

def test_folder_upload():
    """Test batch processing with multiple files from a folder."""
    api_url = "http://localhost:8000/api/batch/analyze-all-with-preview"
    
    # Test folder path
    test_folder = Path("/tmp/test_batch_folder")
    
    # Get all txt and docx files
    files_to_process = list(test_folder.glob("*.txt")) + list(test_folder.glob("*.docx"))
    
    print(f"Found {len(files_to_process)} files to process:")
    for f in files_to_process:
        print(f"  - {f.name}")
    
    # Prepare the request
    files = []
    for file_path in files_to_process:
        files.append(('files', (file_path.name, open(file_path, 'rb'), 'application/octet-stream')))
    
    data = {
        'schema_template_id': 'default_product_feedback',
        'extract_customer_info': 'true',
        'export_format': 'xlsx'
    }
    
    print("\nSending batch processing request...")
    
    try:
        response = requests.post(api_url, files=files, data=data, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"\nProcessed {len(result['table_data'])} files successfully!")
        print("\nExtracted customer names:")
        for item in result['table_data']:
            print(f"  - {item['source']}: {item['customer_name']}")
        
        # Save the spreadsheet
        if 'spreadsheet_base64' in result:
            spreadsheet_data = base64.b64decode(result['spreadsheet_base64'])
            output_path = Path("batch_results.xlsx")
            output_path.write_bytes(spreadsheet_data)
            print(f"\nSpreadsheet saved to: {output_path}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\nError: {e}")
        return False
    finally:
        # Close all file handles
        for _, file_info in files:
            file_info[1].close()

if __name__ == "__main__":
    success = test_folder_upload()
    exit(0 if success else 1)