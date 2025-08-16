#!/usr/bin/env python3
"""
Test AI-Powered Sentiment Analysis with Grok
"""

from live_data_service import live_data
import time

def test_ai_sentiment():
    print("🤖 TESTING AI-POWERED SENTIMENT ANALYSIS")
    print("=" * 70)
    
    # Test tickers
    test_tickers = ["AAPL", "TSLA", "NVDA"]
    
    for ticker in test_tickers:
        print(f"\n🔍 AI Sentiment Analysis for {ticker}:")
        print("-" * 50)
        
        try:
            # Get AI-powered sentiment
            sentiment_data = live_data.get_market_sentiment(ticker)
            
            print(f"🎯 Overall Sentiment: {sentiment_data['sentiment'].upper()}")
            print(f"📊 Sentiment Score: {sentiment_data['sentiment_score']:+.3f}")
            print(f"🎯 Confidence: {sentiment_data['confidence']:.1%}")
            print(f"💭 Reasoning: {sentiment_data['reasoning']}")
            
            print(f"\n📰 News Analysis:")
            print(f"   • News Sentiment: {sentiment_data['news_sentiment']}")
            print(f"   • Articles Analyzed: {sentiment_data['news_count']}")
            
            print(f"\n📱 Social Media Analysis:")
            print(f"   • Social Sentiment: {sentiment_data['social_sentiment']}")
            print(f"   • Social Mentions: {sentiment_data['social_mentions']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(2)  # Be nice to APIs
    
    print("\n" + "=" * 70)
    print("🎯 AI SENTIMENT FEATURES:")
    print("✅ Grok AI-powered analysis")
    print("✅ Financial NLP understanding")
    print("✅ News + Social media integration")
    print("✅ Confidence scoring")
    print("✅ Detailed reasoning")
    print("✅ Multi-source validation")

if __name__ == "__main__":
    test_ai_sentiment()
