#!/usr/bin/env python3
"""
Demo: Cryptocurrency Analysis and Trading
Shows how the system analyzes crypto markets with enhanced factors
"""

import time
from add_stock_service import add_stock_to_dashboard, analyze_market_conditions


def demo_crypto_analysis():
    """Demonstrate crypto-specific market analysis."""
    
    print("₿ CRYPTOCURRENCY ANALYSIS DEMO")
    print("=" * 80)
    print("Enhanced market analysis for crypto with:")
    print("• Extreme RSI thresholds (25/75 vs 30/70)")
    print("• Crypto-specific sentiment (FOMO, Fear)")
    print("• Regulatory news impact")
    print("• Whale activity tracking")
    print("• BTC dominance effects")
    print("• Alt season detection")
    print("=" * 80)
    
    # Major cryptocurrencies to analyze
    crypto_assets = [
        "BTC-USD", "ETH-USD", "BNB-USD", "XRP-USD", 
        "ADA-USD", "SOL-USD", "DOT-USD", "MATIC-USD"
    ]
    
    print("\n🔍 ANALYZING CRYPTO MARKET CONDITIONS")
    print("-" * 60)
    
    long_recommendations = []
    short_recommendations = []
    
    # Analyze each crypto
    for ticker in crypto_assets:
        print(f"\n₿ Analyzing {ticker.replace('-USD', '')}...")
        
        # Get crypto-enhanced market analysis
        analysis = analyze_market_conditions(ticker)
        
        # Display analysis
        print(f"   🎯 Recommendation: {analysis['recommendation']}")
        print(f"   📈 Confidence: {analysis['confidence']:.1%}")
        print(f"   📋 Crypto Technical Data:")
        tech = analysis['technical_data']
        
        # Show crypto-specific metrics
        print(f"      • RSI: {tech['rsi']:.1f} ({'Oversold' if tech['rsi'] < 25 else 'Overbought' if tech['rsi'] > 75 else 'Neutral'})")
        print(f"      • Trend: {tech['trend_direction'].title()}")
        print(f"      • Price vs MA200: {tech['price_vs_ma200']:+.1%}")
        print(f"      • Volatility: {tech['volatility']:.1%} (High)")
        print(f"      • Sentiment: {tech['news_sentiment'].title()}")
        print(f"      • Market Regime: {tech['market_regime'].replace('_', ' ').title()}")
        
        # Crypto-specific factors
        if 'btc_dominance' in tech:
            print(f"      • BTC Dominance: {tech['btc_dominance']:.1f}%")
            print(f"      • DeFi Activity: {tech['defi_activity'].title()}")
            print(f"      • Regulatory News: {tech['regulatory_news'].title()}")
            print(f"      • Whale Activity: {tech['whale_activity'].title()}")
        
        print(f"   💡 Reasoning: {' | '.join(analysis['reasoning'])}")
        
        # Categorize recommendations
        if analysis['recommendation'] == 'LONG':
            long_recommendations.append((ticker, analysis))
        else:
            short_recommendations.append((ticker, analysis))
        
        time.sleep(0.5)
    
    print("\n" + "=" * 80)
    print("📊 CRYPTO ANALYSIS SUMMARY")
    print("=" * 80)
    
    print(f"\n📈 LONG RECOMMENDATIONS ({len(long_recommendations)}):")
    for ticker, analysis in long_recommendations:
        crypto_name = ticker.replace('-USD', '')
        reasons = analysis['reasoning'][:2]
        print(f"   {crypto_name}: {analysis['confidence']:.0%} confidence - {' | '.join(reasons)}")
    
    print(f"\n📉 SHORT RECOMMENDATIONS ({len(short_recommendations)}):")
    for ticker, analysis in short_recommendations:
        crypto_name = ticker.replace('-USD', '')
        reasons = analysis['reasoning'][:2]
        print(f"   {crypto_name}: {analysis['confidence']:.0%} confidence - {' | '.join(reasons)}")
    
    print("\n" + "=" * 80)
    print("🚀 ADDING CRYPTO TO DASHBOARD WITH ENHANCED ANALYSIS")
    print("=" * 80)
    
    # Add a mix of cryptos
    cryptos_to_add = ["SOL-USD", "ADA-USD", "MATIC-USD", "XRP-USD"]
    
    for ticker in cryptos_to_add:
        crypto_name = ticker.replace('-USD', '')
        print(f"\n₿ Adding {crypto_name} with crypto-enhanced analysis...")
        success = add_stock_to_dashboard(ticker)
        if success:
            print(f"✅ {crypto_name} successfully added!")
        else:
            print(f"❌ Failed to add {crypto_name}")
        time.sleep(1)
    
    print("\n" + "=" * 80)
    print("📊 FINAL CRYPTO PORTFOLIO STATUS")
    print("=" * 80)
    
    # Show current crypto holdings
    import json
    import os
    
    try:
        with open("public/data/stocks_long.json", 'r') as f:
            long_data = json.load(f)
        with open("public/data/stocks_short.json", 'r') as f:
            short_data = json.load(f)
        
        # Filter crypto assets
        crypto_longs = [s for s in long_data if '-USD' in s['ticker']]
        crypto_shorts = [s for s in short_data if '-USD' in s['ticker']]
        
        print(f"\n₿ CRYPTO LONG POSITIONS ({len(crypto_longs)}):")
        for crypto in crypto_longs:
            crypto_name = crypto['ticker'].replace('-USD', '')
            print(f"   {crypto_name}: {crypto['strategy']} "
                  f"({crypto['confidence']:.1f}% confidence, {crypto['upsidePotential']:+.1f}% upside)")
        
        print(f"\n📉 CRYPTO SHORT POSITIONS ({len(crypto_shorts)}):")
        for crypto in crypto_shorts:
            crypto_name = crypto['ticker'].replace('-USD', '')
            print(f"   {crypto_name}: {crypto['strategy']} "
                  f"({crypto['confidence']:.1f}% confidence, {crypto['upsidePotential']:+.1f}% downside)")
        
        total_crypto = len(crypto_longs) + len(crypto_shorts)
        total_stocks = len(long_data) + len(short_data) - total_crypto
        
        print(f"\n📊 Portfolio Summary:")
        print(f"   • Total Crypto Assets: {total_crypto}")
        print(f"   • Total Stock Assets: {total_stocks}")
        print(f"   • Total Assets Tracked: {len(long_data) + len(short_data)}")
        
    except Exception as e:
        print(f"❌ Error reading data: {e}")
    
    print("\n" + "=" * 80)
    print("🎯 CRYPTO-ENHANCED FEATURES DEMONSTRATED:")
    print("✅ Extreme RSI thresholds for crypto volatility")
    print("✅ FOMO/Fear sentiment analysis")
    print("✅ Regulatory news impact assessment")
    print("✅ Whale activity tracking")
    print("✅ BTC dominance period detection")
    print("✅ Alt season environment recognition")
    print("✅ Enhanced volatility handling")
    print("✅ Crypto-specific strategy selection")
    print("✅ 24/7 market analysis capability")
    print("\n🌐 Visit http://localhost:3000 to see your crypto portfolio!")


def show_crypto_vs_stock_differences():
    """Show the differences in analysis between crypto and stocks."""
    
    print("\n" + "=" * 80)
    print("📊 CRYPTO vs STOCK ANALYSIS DIFFERENCES")
    print("=" * 80)
    
    print("\n📈 STOCKS:")
    print("   • RSI Thresholds: 30 (oversold) / 70 (overbought)")
    print("   • Volatility Range: 15-45% annually")
    print("   • Sentiment: Bullish/Bearish/Neutral")
    print("   • Market Regimes: Bull/Bear/Choppy")
    print("   • Price vs MA200: ±30% range")
    print("   • Analysis Focus: Fundamentals + Technicals")
    
    print("\n₿ CRYPTO:")
    print("   • RSI Thresholds: 25 (oversold) / 75 (overbought)")
    print("   • Volatility Range: 30-80% annually")
    print("   • Sentiment: Bullish/Bearish/Neutral/FOMO/Fear")
    print("   • Market Regimes: Crypto Bull/Bear/Alt Season/BTC Dominance")
    print("   • Price vs MA200: ±50% range")
    print("   • Analysis Focus: Technicals + Sentiment + On-chain")
    print("   • Additional Factors:")
    print("     - BTC Dominance (40-60%)")
    print("     - DeFi Activity (High/Medium/Low)")
    print("     - Regulatory News Impact")
    print("     - Whale Activity Tracking")
    
    print("\n🎯 Strategy Selection Differences:")
    print("   • Crypto favors momentum strategies in alt seasons")
    print("   • BTC dominance periods favor Bitcoin over alts")
    print("   • Higher volatility = more aggressive position sizing")
    print("   • 24/7 markets = continuous analysis capability")


if __name__ == "__main__":
    demo_crypto_analysis()
    show_crypto_vs_stock_differences()
