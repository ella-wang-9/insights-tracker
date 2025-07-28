#!/usr/bin/env python3
"""Check Databricks endpoint status using REST API."""

import os
import requests
import json

# Get credentials
host = os.getenv('DATABRICKS_HOST', '').rstrip('/')
token = os.getenv('DATABRICKS_TOKEN', '')

if not host or not token:
    print("Error: DATABRICKS_HOST and DATABRICKS_TOKEN must be set")
    exit(1)

print(f"Host: {host}")
print(f"Token: {'*' * 10}{token[-4:] if len(token) > 4 else ''}")

# Headers for API requests
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# List all serving endpoints
print("\nListing serving endpoints...")
url = f"{host}/api/2.0/serving-endpoints"

try:
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        endpoints = data.get('endpoints', [])
        
        print(f"\nFound {len(endpoints)} endpoints:\n")
        
        foundation_models = []
        for endpoint in endpoints:
            name = endpoint.get('name', '')
            state = endpoint.get('state', {}).get('ready', 'UNKNOWN')
            
            # Check if it's a foundation model
            if any(model in name.lower() for model in ['llama', 'mixtral', 'dbrx', 'mpt']):
                foundation_models.append((name, state))
                print(f"  {name:<50} {state}")
        
        print(f"\nFoundation models available: {len(foundation_models)}")
        
        # Show ready models
        ready_models = [name for name, state in foundation_models if state == 'READY']
        if ready_models:
            print("\nREADY models:")
            for model in ready_models:
                print(f"  - {model}")
        
    else:
        print(f"Error {response.status_code}: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")