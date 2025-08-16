#!/usr/bin/env python3
"""
Demo: Live Data Integration
Shows real market data, technical indicators, and analysis
"""

from live_data_service import live_data
from add_stock_service import add_stock_to_dashboard, analyze_market_conditions
import time


def demo_live_data_integration():
    """Demonstrate live data integration across all components."""
    
    print("🌐 LIVE DATA INTEGRATION DEMO")
    print("=" * 80)
    print("Replacing ALL mock data with real market feeds!")
    print("=" * 80)
    
    # Test assets
    test_assets = [
        ("AAPL", "Apple Inc."),
        ("GOOGL", "Alphabet Inc."),
        ("BTC-USD", "Bitcoin"),
        ("ETH-USD", "Ethereum")
    ]
    
    print("\n💰 REAL LIVE PRICES")
    print("-" * 50)
    
    for ticker, name in test_assets:
        try:
            price = live_data.get_live_price(ticker)
            company_info = live_data.get_company_info(ticker)
            
            print(f"📊 {ticker} ({company_info['name']})")
            print(f"   💵 Current Price: ${price:,.2f}")
            
            if 'market_cap' in company_info and company_info['market_cap'] > 0:
                market_cap = company_info['market_cap'] / 1e9  # Convert to billions
                print(f"   🏢 Market Cap: ${market_cap:.1f}B")
            
            if 'pe_ratio' in company_info and company_info['pe_ratio']:
                print(f"   📈 P/E Ratio: {company_info['pe_ratio']:.1f}")
                
        except Exception as e:
            print(f"❌ Error for {ticker}: {e}")
        
        time.sleep(0.5)
    
    print("\n📊 REAL TECHNICAL INDICATORS")
    print("-" * 50)
    
    for ticker, name in test_assets[:2]:  # Test first 2 to save time
        try:
            print(f"\n🔍 {ticker} Technical Analysis:")
            indicators = live_data.calculate_technical_indicators(ticker)
            
            print(f"   📈 RSI: {indicators['rsi']:.1f} "
                  f"({'Oversold' if indicators['rsi'] < 30 else 'Overbought' if indicators['rsi'] > 70 else 'Neutral'})")
            print(f"   📊 Trend: {indicators['trend_direction'].title()}")
            print(f"   📉 Price vs SMA200: {indicators['price_vs_sma200']:+.1%}")
            print(f"   🌊 Volatility: {indicators['volatility']:.1%} annually")
            print(f"   💪 ADX (Trend Strength): {indicators['adx']:.1f}")
            print(f"   📊 Volume Ratio: {indicators['volume_ratio']:.1f}x average")
            
            # MACD analysis
            if indicators['macd_histogram'] > 0:
                macd_signal = "Bullish momentum"
            elif indicators['macd_histogram'] < 0:
                macd_signal = "Bearish momentum"
            else:
                macd_signal = "Neutral momentum"
            print(f"   📈 MACD: {macd_signal}")
            
        except Exception as e:
            print(f"❌ Error getting indicators for {ticker}: {e}")
        
        time.sleep(1)
    
    print("\n🧠 COMPREHENSIVE MARKET ANALYSIS")
    print("-" * 50)
    
    # Test comprehensive analysis
    test_ticker = "AAPL"
    print(f"\n🍎 Complete Analysis for {test_ticker}:")
    
    try:
        analysis = analyze_market_conditions(test_ticker)
        
        print(f"   🎯 Recommendation: {analysis['recommendation']}")
        print(f"   📊 Confidence: {analysis['confidence']:.1%}")
        print(f"   💡 Key Factors:")
        
        for reason in analysis['reasoning']:
            print(f"      • {reason}")
        
        tech_data = analysis['technical_data']
        print(f"   📈 Technical Summary:")
        print(f"      • RSI: {tech_data['rsi']:.1f}")
        print(f"      • Trend: {tech_data['trend_direction'].title()}")
        print(f"      • Volatility: {tech_data['volatility']:.1%}")
        print(f"      • Market Regime: {tech_data['market_regime'].replace('_', ' ').title()}")
        
    except Exception as e:
        print(f"❌ Error in market analysis: {e}")
    
    print("\n🚀 ADDING ASSETS WITH LIVE DATA")
    print("-" * 50)
    
    # Add a new asset to demonstrate live integration
    new_assets = ["TSLA", "SOL-USD"]
    
    for ticker in new_assets:
        print(f"\n📈 Adding {ticker} with live data analysis...")
        
        try:
            # Show live price first
            live_price = live_data.get_live_price(ticker)
            print(f"   💰 Live Price: ${live_price:,.2f}")
            
            # Add to dashboard
            success = add_stock_to_dashboard(ticker)
            
            if success:
                print(f"   ✅ {ticker} added successfully with live data!")
            else:
                print(f"   ❌ Failed to add {ticker}")
                
        except Exception as e:
            print(f"   ❌ Error adding {ticker}: {e}")
        
        time.sleep(1)
    
    print("\n📊 LIVE DATA FEATURES SUMMARY")
    print("=" * 80)
    
    print("✅ REAL PRICES:")
    print("   • Live stock prices from Yahoo Finance")
    print("   • Real-time crypto prices (BTC, ETH, etc.)")
    print("   • Automatic price updates with caching")
    
    print("\n✅ REAL TECHNICAL INDICATORS:")
    print("   • RSI calculated from actual price history")
    print("   • Moving averages from real data")
    print("   • MACD, ADX, ATR from live market data")
    print("   • Bollinger Bands and volume analysis")
    
    print("\n✅ REAL COMPANY DATA:")
    print("   • Actual company names and sectors")
    print("   • Real market capitalization")
    print("   • P/E ratios and financial metrics")
    print("   • Beta and dividend yield data")
    
    print("\n✅ ENHANCED ANALYSIS:")
    print("   • Market sentiment from news (basic)")
    print("   • Volatility-based forecasting")
    print("   • Volume scaled by market cap")
    print("   • Realistic target prices")
    
    print("\n✅ SMART CACHING:")
    print("   • 5-minute cache to reduce API calls")
    print("   • Fallback to mock data if APIs fail")
    print("   • Optimized for performance")
    
    print("\n🎯 NEXT LEVEL FEATURES AVAILABLE:")
    print("   • News API integration for sentiment")
    print("   • Alpha Vantage for more indicators")
    print("   • CoinGecko for enhanced crypto data")
    print("   • Social media sentiment analysis")
    
    print("\n🌐 Your dashboard now uses 100% LIVE MARKET DATA!")
    print("Visit http://localhost:3000 to see real prices and analysis!")


if __name__ == "__main__":
    demo_live_data_integration()
