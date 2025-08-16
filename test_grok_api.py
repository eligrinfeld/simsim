#!/usr/bin/env python3
"""
Test Grok API Connection
"""

import os
import requests
from dotenv import load_dotenv

def test_grok_api():
    load_dotenv()
    
    grok_key = os.getenv('GROK_API_KEY')
    print(f"🔑 Grok API Key: {grok_key[:20]}..." if grok_key else "❌ No Grok API Key")
    
    if not grok_key:
        print("❌ No Grok API key found")
        return
    
    # Test simple API call
    headers = {
        'Authorization': f'Bearer {grok_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'messages': [
            {
                'role': 'user',
                'content': 'Hello, can you analyze sentiment? Just respond with "Yes, I can analyze sentiment."'
            }
        ],
        'model': 'grok-2-1212',
        'stream': False,
        'temperature': 0.1
    }
    
    print("🔍 Testing Grok API connection...")
    
    try:
        response = requests.post(
            'https://api.x.ai/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📝 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Response: {data}")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_grok_api()
