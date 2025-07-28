#!/usr/bin/env python3
"""Test Databricks REST API directly."""

import os
import requests
import json
import time

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

# Test with REST API
endpoint = "databricks-meta-llama-3-1-8b-instruct"
url = f"{host}/serving-endpoints/{endpoint}/invocations"

payload = {
    "messages": [
        {
            "role": "user",
            "content": "Reply with the word 'hello' only."
        }
    ],
    "max_tokens": 10,
    "temperature": 0.0
}

print(f"\nTesting {endpoint} via REST API...")
print(f"URL: {url}")
print("Sending request...")

start = time.time()

try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    elapsed = time.time() - start
    
    print(f"\nResponse received in {elapsed:.1f} seconds")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")
        
except requests.exceptions.Timeout:
    elapsed = time.time() - start
    print(f"\n❌ Timeout after {elapsed:.1f} seconds")
except Exception as e:
    print(f"\n❌ Error: {e}")