#!/usr/bin/env python3
"""
Test Live Data Service
"""

from live_data_service import live_data

def test_live_data():
    print("🧪 Testing Live Data Service...")
    print("=" * 50)
    
    # Test live prices
    print("\n📊 Live Prices:")
    tickers = ["AAPL", "NVDA", "BTC-USD", "ETH-USD"]
    
    for ticker in tickers:
        try:
            price = live_data.get_live_price(ticker)
            print(f"   {ticker}: ${price:,.2f}")
        except Exception as e:
            print(f"   {ticker}: Error - {e}")
    
    # Test technical indicators
    print("\n📈 Technical Indicators for AAPL:")
    try:
        indicators = live_data.calculate_technical_indicators('AAPL')
        print(f"   RSI: {indicators['rsi']:.1f}")
        print(f"   Trend: {indicators['trend_direction']}")
        print(f"   Price vs SMA200: {indicators['price_vs_sma200']:+.1%}")
        print(f"   Volatility: {indicators['volatility']:.1%}")
        print(f"   ADX: {indicators['adx']:.1f}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test company info
    print("\n🏢 Company Info for AAPL:")
    try:
        info = live_data.get_company_info('AAPL')
        print(f"   Name: {info['name']}")
        print(f"   Sector: {info['sector']}")
        print(f"   Market Cap: ${info['market_cap']:,}")
        print(f"   P/E Ratio: {info['pe_ratio']:.1f}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n✅ Live data service test complete!")

if __name__ == "__main__":
    test_live_data()
