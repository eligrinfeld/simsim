#!/usr/bin/env python3
"""Test script for X sentiment analysis integration."""

import asyncio
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the server path for imports
sys.path.append('apps/event_dashboard')

async def test_grok_x_sentiment(ticker="AAPL"):
    """Test Grok API X sentiment analysis for a specific ticker."""
    
    grok_api_key = os.getenv("GROK_API_KEY")
    
    if not grok_api_key:
        print("❌ GROK_API_KEY not found in environment variables")
        return False
    
    print(f"🧪 Testing X sentiment analysis for {ticker}...")
    print(f"🔑 Using API key: {grok_api_key[:10]}...{grok_api_key[-4:]}")
    
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {grok_api_key}"
    }
    
    prompt = f"""Using your available tools like x_keyword_search or x_semantic_search, fetch the latest 20 posts on X that mention the ticker ${ticker} (sort by Latest mode). Focus on posts from the past 7 days that discuss stock performance, news, or sentiment.

Then, perform the following analysis:

Analyze the overall sentiment of the posts: Categorize them as positive, negative, neutral, or mixed. Provide a sentiment score on a scale of -1 (very bearish) to +1 (very bullish), based on the majority tone.
Determine the overall direction of the stock: Summarize if the consensus points to upward (bullish), downward (bearish), or sideways movement, with key reasons extracted from the posts (e.g., earnings reports, market trends, or events).
If any posts mention or link to a new article (published within the last 7 days), use tools like browse_page or web_search to access and summarize the article. Include the article's title, source, publication date, key points, and how it relates to the stock.
Present your response in a structured format:

Latest Posts Summary: List 5-10 key posts with usernames, dates, and brief excerpts.
Sentiment Analysis: Overall score and breakdown.
Stock Direction: Predicted direction and rationale.
Article Summaries: If applicable, one per mentioned article.
Do not fabricate information; base everything on the searched data."""

    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a financial sentiment analyst with access to X (Twitter) data. Use your tools to search for real posts and provide accurate analysis."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": "grok-4-latest",
        "stream": False,
        "temperature": 0.3
    }
    
    try:
        print("📡 Sending request to Grok API...")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                analysis = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                
                print("✅ X Sentiment Analysis Results:")
                print("=" * 60)
                print(analysis)
                print("=" * 60)
                
                print(f"\n📈 Token Usage:")
                print(f"   Prompt tokens: {usage.get('prompt_tokens', 0)}")
                print(f"   Completion tokens: {usage.get('completion_tokens', 0)}")
                print(f"   Total tokens: {usage.get('total_tokens', 0)}")
                print(f"   Reasoning tokens: {usage.get('completion_tokens_details', {}).get('reasoning_tokens', 0)}")
                
                # Try to extract sentiment score
                sentiment_score = extract_sentiment_score(analysis)
                print(f"\n🎯 Extracted Sentiment Score: {sentiment_score:.2f}")
                
                return True
            else:
                print("❌ No response content from Grok API")
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
        print("❌ Request timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def extract_sentiment_score(analysis_text: str) -> float:
    """Extract numerical sentiment score from Grok's analysis text."""
    try:
        import re
        
        # Look for sentiment score patterns in the text
        score_patterns = [
            r"sentiment score[:\s]+([+-]?\d*\.?\d+)",
            r"score of ([+-]?\d*\.?\d+)",
            r"overall score[:\s]+([+-]?\d*\.?\d+)",
            r"([+-]?\d*\.?\d+).*?(?:bullish|bearish)",
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, analysis_text.lower())
            if match:
                score = float(match.group(1))
                # Ensure score is within -1 to +1 range
                return max(-1.0, min(1.0, score))
        
        # Look for qualitative sentiment indicators
        text_lower = analysis_text.lower()
        
        positive_indicators = ["bullish", "positive", "optimistic", "upward", "buy", "strong", "growth"]
        negative_indicators = ["bearish", "negative", "pessimistic", "downward", "sell", "weak", "decline"]
        
        pos_count = sum(1 for word in positive_indicators if word in text_lower)
        neg_count = sum(1 for word in negative_indicators if word in text_lower)
        
        if pos_count > neg_count:
            return 0.5  # Moderately positive
        elif neg_count > pos_count:
            return -0.5  # Moderately negative
        else:
            return 0.0  # Neutral
            
    except Exception as e:
        print(f"❌ Error extracting sentiment score: {e}")
        return 0.0

async def test_sentiment_endpoints():
    """Test the sentiment API endpoints."""
    print("\n🧪 Testing sentiment API endpoints...")
    
    base_url = "http://127.0.0.1:8010"
    
    try:
        # Test all sentiment scores
        response = requests.get(f"{base_url}/sentiment", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ All sentiment scores:")
            for symbol, info in data.items():
                print(f"   {symbol}: {info['current_score']:.2f} ({info['total_analyses']} analyses)")
        else:
            print(f"❌ Failed to get sentiment scores: {response.status_code}")
        
        # Test specific symbol sentiment
        symbol = "AAPL"
        response = requests.get(f"{base_url}/sentiment/{symbol}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ {symbol} sentiment details:")
            print(f"   Current score: {data['current_score']:.2f}")
            print(f"   Total scores: {data['count']}")
            print(f"   Recent scores: {len(data['sentiment_scores'])}")
        else:
            print(f"❌ Failed to get {symbol} sentiment: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")

async def main():
    """Main test function."""
    print("🚀 X Sentiment Analysis Integration Test\n")
    
    # Test 1: Grok API X sentiment analysis
    success = await test_grok_x_sentiment("AAPL")
    
    if success:
        print("\n🎉 Grok X sentiment analysis successful!")
    else:
        print("\n❌ Grok X sentiment analysis failed!")
    
    # Test 2: API endpoints (if server is running)
    await test_sentiment_endpoints()
    
    print("\n💡 Integration Notes:")
    print("   - X sentiment analysis runs every 2 hours to manage API costs")
    print("   - Sentiment scores are cumulative and stored for charting")
    print("   - CEP rules correlate sentiment with price movements")
    print("   - Strong sentiment (≥0.7) triggers special events")
    print("   - Frontend shows sentiment overlay on price charts")
    
    print("\n✅ X Sentiment Integration Test Complete!")

if __name__ == "__main__":
    asyncio.run(main())
