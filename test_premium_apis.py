#!/usr/bin/env python3
"""
Test Premium API Integration
"""

from live_data_service import live_data
import time

def test_premium_apis():
    print("🔑 TESTING PREMIUM API INTEGRATION")
    print("=" * 60)
    
    # Test tickers
    test_tickers = ["AAPL", "TSLA", "BTC-USD"]
    
    print("\n💰 PREMIUM PRICE FEEDS")
    print("-" * 40)
    
    for ticker in test_tickers:
        print(f"\n📊 Testing {ticker}:")
        try:
            price = live_data.get_live_price(ticker)
            print(f"   💵 Price: ${price:,.2f}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        time.sleep(1)
    
    print("\n📰 REAL NEWS SENTIMENT")
    print("-" * 40)
    
    for ticker in ["AAPL", "TSLA"]:  # Test news for stocks only
        print(f"\n📰 Testing sentiment for {ticker}:")
        try:
            sentiment = live_data.get_market_sentiment(ticker)
            print(f"   🎯 Sentiment: {sentiment['sentiment']}")
            print(f"   📊 Score: {sentiment['sentiment_score']:+.2f}")
            print(f"   📰 News Articles: {sentiment['news_count']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        time.sleep(2)  # Be nice to APIs
    
    print("\n✅ Premium API test complete!")

if __name__ == "__main__":
    test_premium_apis()
