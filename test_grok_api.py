#!/usr/bin/env python3
"""Test script for Grok API connection."""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_grok_api():
    """Test Grok API connection using the provided curl equivalent."""
    
    # Get API key from environment
    api_key = os.getenv("GROK_API_KEY")
    
    if not api_key:
        print("❌ GROK_API_KEY not found in environment variables")
        print("💡 Make sure to add GROK_API_KEY to your .env file")
        return False
    
    print("🧪 Testing Grok API connection...")
    print(f"🔑 Using API key: {api_key[:10]}...{api_key[-4:]}")
    
    # API endpoint
    url = "https://api.x.ai/v1/chat/completions"
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Request payload
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a test assistant."
            },
            {
                "role": "user",
                "content": "Testing. Just say hi and hello world and nothing else."
            }
        ],
        "model": "grok-4-latest",
        "stream": False,
        "temperature": 0
    }
    
    try:
        print("📡 Sending request to Grok API...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract the response message
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0]["message"]["content"]
                print(f"✅ Grok API Response: {message}")
                
                # Print usage info if available
                if "usage" in data:
                    usage = data["usage"]
                    print(f"📈 Token usage: {usage}")
                
                print("🎉 Grok API connection successful!")
                return True
            else:
                print("❌ Unexpected response format")
                print(f"Response: {json.dumps(data, indent=2)}")
                return False
                
        else:
            print(f"❌ API request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON response: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_with_curl():
    """Show the equivalent curl command for testing."""
    api_key = os.getenv("GROK_API_KEY")
    
    if not api_key:
        print("❌ GROK_API_KEY not found in environment variables")
        return
    
    print("\n🔧 Equivalent curl command:")
    print("=" * 50)
    curl_command = f'''curl https://api.x.ai/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer {api_key}" \\
  -d '{{
  "messages": [
    {{
      "role": "system",
      "content": "You are a test assistant."
    }},
    {{
      "role": "user",
      "content": "Testing. Just say hi and hello world and nothing else."
    }}
  ],
  "model": "grok-4-latest",
  "stream": false,
  "temperature": 0
}}'
'''
    print(curl_command)
    print("=" * 50)

if __name__ == "__main__":
    print("🚀 Grok API Connection Test\n")
    
    # Test the API connection
    success = test_grok_api()
    
    # Show curl equivalent
    test_with_curl()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("💡 You can now use Grok API in your applications")
    else:
        print("\n❌ Test failed!")
        print("💡 Check your API key and network connection")
        print("💡 Make sure GROK_API_KEY is set in your .env file")
