#!/usr/bin/env python3
"""Test script for live news integration."""

import asyncio
import os
import requests
from textblob import TextBlob
import feedparser
from datetime import datetime, timedelta

SUPPORTED_SYMBOLS = ["SPY", "QQQ", "AAPL", "MSFT", "TSLA", "NVDA"]
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

def analyze_sentiment(text: str) -> float:
    """Analyze sentiment of text using TextBlob."""
    try:
        blob = TextBlob(text)
        return blob.sentiment.polarity
    except:
        return 0.0

def extract_symbols_from_text(text: str) -> list:
    """Extract stock symbols mentioned in news text."""
    text_upper = text.upper()
    mentioned_symbols = []
    
    # Check for direct symbol mentions
    for symbol in SUPPORTED_SYMBOLS:
        if symbol in text_upper:
            mentioned_symbols.append(symbol)
    
    # Check for company name mentions
    company_names = {
        "AAPL": ["APPLE", "IPHONE", "MAC", "IPAD"],
        "MSFT": ["MICROSOFT", "WINDOWS", "AZURE"],
        "TSLA": ["TESLA", "ELON MUSK", "ELECTRIC VEHICLE"],
        "NVDA": ["NVIDIA", "GPU", "AI CHIP"]
    }
    
    for symbol, names in company_names.items():
        for name in names:
            if name in text_upper and symbol not in mentioned_symbols:
                mentioned_symbols.append(symbol)
                break
    
    return mentioned_symbols if mentioned_symbols else ["SPY"]

async def test_newsapi():
    """Test NewsAPI integration."""
    print("🧪 Testing NewsAPI...")
    
    if not NEWS_API_KEY:
        print("⚠️ No NEWS_API_KEY found - skipping NewsAPI test")
        return []
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "Apple OR iPhone OR Tim Cook",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 5,
            "apiKey": NEWS_API_KEY,
            "from": (datetime.now() - timedelta(hours=6)).isoformat()
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = []
            
            for article in data.get("articles", []):
                if article.get("title") and article.get("description"):
                    text = f"{article['title']} {article['description']}"
                    sentiment = analyze_sentiment(text)
                    symbols = extract_symbols_from_text(text)
                    
                    articles.append({
                        "title": article["title"],
                        "sentiment": sentiment,
                        "symbols": symbols,
                        "source": "NewsAPI"
                    })
                    
                    print(f"📰 {article['title'][:60]}...")
                    print(f"   Sentiment: {sentiment:.2f}, Symbols: {symbols}")
            
            print(f"✅ NewsAPI: Found {len(articles)} articles")
            return articles
        else:
            print(f"❌ NewsAPI error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ NewsAPI exception: {e}")
    
    return []

async def test_alpha_vantage():
    """Test Alpha Vantage News integration."""
    print("\n🧪 Testing Alpha Vantage News...")
    
    if not ALPHA_VANTAGE_KEY:
        print("⚠️ No ALPHA_VANTAGE_API_KEY found - skipping Alpha Vantage test")
        return []
    
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": "AAPL",
            "limit": 5,
            "apikey": ALPHA_VANTAGE_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = []
            
            for item in data.get("feed", []):
                if item.get("title") and item.get("summary"):
                    sentiment_score = float(item.get("overall_sentiment_score", 0))
                    
                    ticker_sentiment = item.get("ticker_sentiment", [])
                    symbols = [t.get("ticker") for t in ticker_sentiment if t.get("ticker") in SUPPORTED_SYMBOLS]
                    if not symbols:
                        symbols = ["SPY"]
                    
                    articles.append({
                        "title": item["title"],
                        "sentiment": sentiment_score,
                        "symbols": symbols,
                        "source": "Alpha Vantage"
                    })
                    
                    print(f"📰 {item['title'][:60]}...")
                    print(f"   Sentiment: {sentiment_score:.2f}, Symbols: {symbols}")
            
            print(f"✅ Alpha Vantage: Found {len(articles)} articles")
            return articles
        else:
            print(f"❌ Alpha Vantage error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Alpha Vantage exception: {e}")
    
    return []

async def test_rss_feeds():
    """Test RSS feed integration."""
    print("\n🧪 Testing RSS Feeds...")

    rss_feeds = [
        "https://feeds.finance.yahoo.com/rss/2.0/headline",
        "https://www.marketwatch.com/rss/topstories"
    ]

    articles = []

    for feed_url in rss_feeds:
        try:
            print(f"📡 Fetching {feed_url}...")
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:3]:  # Limit to 3 articles per feed
                if hasattr(entry, 'title') and hasattr(entry, 'summary'):
                    text = f"{entry.title} {entry.summary}"
                    sentiment = analyze_sentiment(text)
                    symbols = extract_symbols_from_text(text)

                    # Only include if sentiment is strong enough
                    if abs(sentiment) >= 0.1:  # Lower threshold for testing
                        articles.append({
                            "title": entry.title,
                            "sentiment": sentiment,
                            "symbols": symbols,
                            "source": feed.feed.get('title', 'RSS Feed')
                        })

                        print(f"📰 {entry.title[:60]}...")
                        print(f"   Sentiment: {sentiment:.2f}, Symbols: {symbols}")

        except Exception as e:
            print(f"❌ RSS feed error for {feed_url}: {e}")
            continue

    print(f"✅ RSS Feeds: Found {len(articles)} articles")
    return articles

async def main():
    """Main test function."""
    print("🚀 Testing Live News Integration\n")
    
    # Test all news sources
    newsapi_articles = await test_newsapi()
    alpha_articles = await test_alpha_vantage()
    rss_articles = await test_rss_feeds()
    
    total_articles = len(newsapi_articles) + len(alpha_articles) + len(rss_articles)
    print(f"\n📊 Total articles found: {total_articles}")
    
    if total_articles == 0:
        print("\n💡 To test with real data, set environment variables:")
        print("   export NEWS_API_KEY='your_newsapi_key'")
        print("   export ALPHA_VANTAGE_API_KEY='your_alphavantage_key'")
        print("\n   Get free keys from:")
        print("   - NewsAPI: https://newsapi.org/")
        print("   - Alpha Vantage: https://www.alphavantage.co/")
    
    print("\n✅ News integration test complete!")

if __name__ == "__main__":
    asyncio.run(main())
