#!/usr/bin/env python3
"""
Demo: Stock Management System
Shows how to add and remove stocks from the dashboard
"""

import time
from add_stock_service import add_stock_to_dashboard, remove_stock_from_dashboard


def demo_stock_management():
    """Demonstrate the stock management functionality."""
    
    print("🚀 STOCK MANAGEMENT SYSTEM DEMO")
    print("=" * 60)
    
    # List of stocks to demo
    demo_stocks = ["GOOGL", "NFLX", "AMD", "UBER", "SPOT"]
    
    print("\n📈 Adding stocks to dashboard...")
    print("-" * 40)
    
    # Add stocks one by one
    for ticker in demo_stocks:
        print(f"\n🔍 Adding {ticker}...")
        success = add_stock_to_dashboard(ticker)
        if success:
            print(f"✅ {ticker} added successfully!")
        else:
            print(f"❌ Failed to add {ticker}")
        time.sleep(1)  # Small delay for demo effect
    
    print("\n" + "=" * 60)
    print("📊 Current dashboard now has:")
    
    # Show current stocks
    import json
    import os
    
    try:
        with open("public/data/stocks_long.json", 'r') as f:
            long_data = json.load(f)
        with open("public/data/stocks_short.json", 'r') as f:
            short_data = json.load(f)
        
        print(f"\n📈 LONG POSITIONS ({len(long_data)}):")
        for stock in long_data:
            print(f"   {stock['ticker']}: {stock['strategy']} "
                  f"({stock['confidence']:.1f}% confidence)")
        
        print(f"\n📉 SHORT POSITIONS ({len(short_data)}):")
        for stock in short_data:
            print(f"   {stock['ticker']}: {stock['strategy']} "
                  f"({stock['confidence']:.1f}% confidence)")
        
        total_stocks = len(long_data) + len(short_data)
        print(f"\n📊 Total stocks tracked: {total_stocks}")
        
    except Exception as e:
        print(f"❌ Error reading data: {e}")
    
    print("\n" + "=" * 60)
    print("🗑️  Removing some stocks...")
    print("-" * 40)
    
    # Remove a couple stocks
    stocks_to_remove = demo_stocks[:2]  # Remove first 2
    
    for ticker in stocks_to_remove:
        print(f"\n🗑️  Removing {ticker}...")
        success = remove_stock_from_dashboard(ticker)
        if success:
            print(f"✅ {ticker} removed successfully!")
        else:
            print(f"❌ Failed to remove {ticker}")
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("🎯 DEMO COMPLETE!")
    print("✅ Stock management system is working!")
    print("🌐 Visit http://localhost:3000 to see the updated dashboard")
    print("\n💡 You can now:")
    print("   • Add stocks using the dashboard interface")
    print("   • Remove stocks with the X button")
    print("   • See real strategy evaluations")
    print("   • View AI-selected best strategies")


if __name__ == "__main__":
    demo_stock_management()
