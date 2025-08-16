#!/usr/bin/env python3
"""
Demo: Market Analysis-Based Stock Recommendations
Shows how the system analyzes market conditions to determine LONG vs SHORT positions
"""

import time
from add_stock_service import add_stock_to_dashboard, remove_stock_from_dashboard, analyze_market_conditions


def demo_market_analysis():
    """Demonstrate market analysis for long/short decisions."""
    
    print("🧠 MARKET ANALYSIS DEMO")
    print("=" * 80)
    print("Showing how the system analyzes market conditions to determine LONG vs SHORT positions")
    print("Based on: RSI, Trend Direction, Sentiment, Support/Resistance, Market Regime")
    print("=" * 80)
    
    # Test stocks to analyze
    test_stocks = ["PLTR", "ZM", "SNOW", "RBLX", "DOCU", "CRWD"]
    
    print("\n🔍 ANALYZING MARKET CONDITIONS FOR MULTIPLE STOCKS")
    print("-" * 60)
    
    long_recommendations = []
    short_recommendations = []
    
    # Analyze each stock
    for ticker in test_stocks:
        print(f"\n📊 Analyzing {ticker}...")
        
        # Get market analysis
        analysis = analyze_market_conditions(ticker)
        
        # Display analysis
        print(f"   🎯 Recommendation: {analysis['recommendation']}")
        print(f"   📈 Confidence: {analysis['confidence']:.1%}")
        print(f"   📋 Technical Data:")
        tech = analysis['technical_data']
        print(f"      • RSI: {tech['rsi']:.1f} ({'Oversold' if tech['rsi'] < 30 else 'Overbought' if tech['rsi'] > 70 else 'Neutral'})")
        print(f"      • Trend: {tech['trend_direction'].title()}")
        print(f"      • Price vs MA200: {tech['price_vs_ma200']:+.1%}")
        print(f"      • Sentiment: {tech['news_sentiment'].title()}")
        print(f"      • Market Regime: {tech['market_regime'].replace('_', ' ').title()}")
        print(f"      • Support/Resistance: {tech['support_resistance'].replace('_', ' ').title()}")
        print(f"   💡 Reasoning: {' | '.join(analysis['reasoning'])}")
        
        # Categorize recommendations
        if analysis['recommendation'] == 'LONG':
            long_recommendations.append((ticker, analysis))
        else:
            short_recommendations.append((ticker, analysis))
        
        time.sleep(0.5)  # Small delay for readability
    
    print("\n" + "=" * 80)
    print("📊 ANALYSIS SUMMARY")
    print("=" * 80)
    
    print(f"\n📈 LONG RECOMMENDATIONS ({len(long_recommendations)}):")
    for ticker, analysis in long_recommendations:
        reasons = analysis['reasoning'][:2]  # Show top 2 reasons
        print(f"   {ticker}: {analysis['confidence']:.0%} confidence - {' | '.join(reasons)}")
    
    print(f"\n📉 SHORT RECOMMENDATIONS ({len(short_recommendations)}):")
    for ticker, analysis in short_recommendations:
        reasons = analysis['reasoning'][:2]  # Show top 2 reasons
        print(f"   {ticker}: {analysis['confidence']:.0%} confidence - {' | '.join(reasons)}")
    
    print("\n" + "=" * 80)
    print("🚀 ADDING STOCKS TO DASHBOARD WITH MARKET-BASED POSITIONING")
    print("=" * 80)
    
    # Add a few stocks to demonstrate
    stocks_to_add = test_stocks[:4]  # Add first 4 stocks
    
    for ticker in stocks_to_add:
        print(f"\n🔍 Adding {ticker} with full market analysis...")
        success = add_stock_to_dashboard(ticker)
        if success:
            print(f"✅ {ticker} successfully added!")
        else:
            print(f"❌ Failed to add {ticker}")
        time.sleep(1)
    
    print("\n" + "=" * 80)
    print("📊 FINAL DASHBOARD STATUS")
    print("=" * 80)
    
    # Show current dashboard
    import json
    import os
    
    try:
        with open("public/data/stocks_long.json", 'r') as f:
            long_data = json.load(f)
        with open("public/data/stocks_short.json", 'r') as f:
            short_data = json.load(f)
        
        print(f"\n📈 LONG POSITIONS ({len(long_data)}):")
        for stock in long_data[-6:]:  # Show last 6 added
            print(f"   {stock['ticker']}: {stock['strategy']} "
                  f"({stock['confidence']:.1f}% confidence, {stock['upsidePotential']:+.1f}% upside)")
        
        print(f"\n📉 SHORT POSITIONS ({len(short_data)}):")
        for stock in short_data:
            print(f"   {stock['ticker']}: {stock['strategy']} "
                  f"({stock['confidence']:.1f}% confidence, {stock['upsidePotential']:+.1f}% downside)")
        
        total_stocks = len(long_data) + len(short_data)
        print(f"\n📊 Total stocks tracked: {total_stocks}")
        
    except Exception as e:
        print(f"❌ Error reading data: {e}")
    
    print("\n" + "=" * 80)
    print("🎯 MARKET ANALYSIS FEATURES DEMONSTRATED:")
    print("✅ RSI-based overbought/oversold analysis")
    print("✅ Trend direction confirmation")
    print("✅ News sentiment integration")
    print("✅ Support/resistance level analysis")
    print("✅ Market regime assessment")
    print("✅ Multi-factor scoring for LONG/SHORT decisions")
    print("✅ Strategy selection based on market conditions")
    print("✅ Confidence-weighted performance adjustments")
    print("\n🌐 Visit http://localhost:3000 to see the updated dashboard!")


if __name__ == "__main__":
    demo_market_analysis()
