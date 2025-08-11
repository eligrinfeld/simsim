#!/usr/bin/env python3
"""Test script for live macro economic data integration."""

import asyncio
import os
import requests
from datetime import datetime, timedelta

FRED_API_KEY = os.getenv("FRED_API_KEY")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

async def test_fred_api():
    """Test FRED API integration."""
    print("🧪 Testing FRED API...")
    
    if not FRED_API_KEY:
        print("⚠️ No FRED_API_KEY found - skipping FRED test")
        return []
    
    # Test key economic indicators
    indicators = [
        ("CPIAUCSL", "Consumer Price Index"),
        ("UNRATE", "Unemployment Rate"),
        ("FEDFUNDS", "Federal Funds Rate"),
        ("GDPC1", "Real GDP")
    ]
    
    economic_data = []
    
    for series_id, name in indicators:
        try:
            url = f"https://api.stlouisfed.org/fred/series/observations"
            params = {
                "series_id": series_id,
                "api_key": FRED_API_KEY,
                "file_type": "json",
                "limit": 1,
                "sort_order": "desc"
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                observations = data.get("observations", [])
                
                if observations:
                    latest = observations[0]
                    value = latest.get("value")
                    if value != ".":  # FRED uses "." for missing data
                        economic_data.append({
                            "indicator": name,
                            "series_id": series_id,
                            "date": latest.get("date"),
                            "value": float(value),
                            "source": "FRED"
                        })
                        
                        print(f"📊 {name}: {value} ({latest.get('date')})")
            else:
                print(f"❌ FRED API error for {series_id}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ FRED API exception for {series_id}: {e}")
            continue
    
    print(f"✅ FRED: Found {len(economic_data)} indicators")
    return economic_data

async def test_alpha_vantage_economic():
    """Test Alpha Vantage economic indicators."""
    print("\n🧪 Testing Alpha Vantage Economic Data...")
    
    if not ALPHA_VANTAGE_KEY:
        print("⚠️ No ALPHA_VANTAGE_API_KEY found - skipping Alpha Vantage test")
        return []
    
    # Test a few key indicators (limited by API rate limits)
    indicators = [
        ("REAL_GDP", "Real GDP"),
        ("CPI", "Consumer Price Index")
    ]
    
    economic_data = []
    
    for indicator_code, indicator_name in indicators:
        try:
            print(f"📡 Fetching {indicator_name}...")
            url = "https://www.alphavantage.co/query"
            params = {
                "function": indicator_code,
                "apikey": ALPHA_VANTAGE_KEY,
                "datatype": "json"
            }
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                # Alpha Vantage has different response structures
                if "data" in data:
                    indicator_data = data["data"]
                    if isinstance(indicator_data, list) and len(indicator_data) > 0:
                        latest = indicator_data[0]
                        economic_data.append({
                            "indicator": indicator_name,
                            "code": indicator_code,
                            "date": latest.get("date"),
                            "value": float(latest.get("value", 0)) if latest.get("value") else None,
                            "source": "Alpha Vantage"
                        })
                        
                        print(f"📊 {indicator_name}: {latest.get('value')} ({latest.get('date')})")
                else:
                    print(f"⚠️ Unexpected response structure for {indicator_code}")
                    print(f"   Keys: {list(data.keys())}")
            else:
                print(f"❌ Alpha Vantage error for {indicator_code}: {response.status_code}")
            
            # Rate limit - wait between calls
            await asyncio.sleep(12)
            
        except Exception as e:
            print(f"❌ Alpha Vantage exception for {indicator_code}: {e}")
            continue
    
    print(f"✅ Alpha Vantage: Found {len(economic_data)} indicators")
    return economic_data

def calculate_surprise(current_value: float, historical_values: list) -> float:
    """Calculate economic surprise (z-score)."""
    if not historical_values or len(historical_values) < 2:
        return 0.0
    
    historical_avg = sum(historical_values) / len(historical_values)
    historical_std = (sum((x - historical_avg) ** 2 for x in historical_values) / len(historical_values)) ** 0.5
    
    if historical_std == 0:
        return 0.0
    
    return (current_value - historical_avg) / historical_std

async def test_economic_calendar():
    """Test economic calendar functionality."""
    print("\n🧪 Testing Economic Calendar...")
    
    # Simulate some economic data with surprises
    mock_data = [
        {"indicator": "CPI", "value": 3.2, "historical": [2.8, 2.9, 3.0, 3.1]},
        {"indicator": "Unemployment", "value": 3.8, "historical": [4.0, 4.1, 3.9, 4.0]},
        {"indicator": "GDP Growth", "value": 2.8, "historical": [2.1, 2.3, 2.2, 2.4]}
    ]
    
    macro_events = []
    
    for data in mock_data:
        surprise = calculate_surprise(data["value"], data["historical"])
        
        if abs(surprise) >= 1.5:  # Significant surprise
            magnitude = "High" if abs(surprise) >= 2.5 else "Medium"
            direction = "positive" if surprise > 0 else "negative"
            
            macro_events.append({
                "indicator": data["indicator"],
                "value": data["value"],
                "surprise": surprise,
                "magnitude": magnitude,
                "direction": direction
            })
            
            print(f"🚨 {data['indicator']}: {data['value']} | Surprise: {surprise:.2f} | {magnitude}")
    
    print(f"✅ Economic Calendar: Found {len(macro_events)} significant events")
    return macro_events

async def main():
    """Main test function."""
    print("🚀 Testing Live Macro Economic Data Integration\n")
    
    # Test all data sources
    fred_data = await test_fred_api()
    alpha_data = await test_alpha_vantage_economic()
    calendar_events = await test_economic_calendar()
    
    total_indicators = len(fred_data) + len(alpha_data)
    total_events = len(calendar_events)
    
    print(f"\n📊 Summary:")
    print(f"   Economic Indicators: {total_indicators}")
    print(f"   Significant Events: {total_events}")
    
    if total_indicators == 0:
        print("\n💡 To test with real data, set environment variables:")
        print("   export FRED_API_KEY='your_fred_key'")
        print("   export ALPHA_VANTAGE_API_KEY='your_alphavantage_key'")
        print("\n   Get free keys from:")
        print("   - FRED: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("   - Alpha Vantage: https://www.alphavantage.co/")
    
    print("\n✅ Macro economic data integration test complete!")

if __name__ == "__main__":
    asyncio.run(main())
