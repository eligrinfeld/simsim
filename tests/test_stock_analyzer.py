import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the stock analyzer to the path
stock_analyzer_path = os.path.join(os.path.dirname(__file__), '..', 'apps', 'stock_analyzer')
sys.path.insert(0, stock_analyzer_path)

# Import from the stock analyzer app
import importlib.util
spec = importlib.util.spec_from_file_location("stock_app", os.path.join(stock_analyzer_path, "app.py"))
stock_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stock_app)

FactorScorer = stock_app.FactorScorer
TechnicalAnalyzer = stock_app.TechnicalAnalyzer
DataProvider = stock_app.DataProvider

def test_factor_scorer_trend():
    # Test trend scoring
    assert FactorScorer.score_trend(110, 100, 0.5) == 5  # Price above MA200, positive slope
    assert FactorScorer.score_trend(110, 100, -0.1) == 4  # Price above MA200, negative slope
    assert FactorScorer.score_trend(90, 100, 0.0) == 3   # Price below MA200, flat slope
    assert FactorScorer.score_trend(90, 100, -0.5) == 1  # Price below MA200, negative slope

def test_factor_scorer_rsi():
    # Test RSI scoring
    assert FactorScorer.score_rsi(50) == 5   # Neutral zone
    assert FactorScorer.score_rsi(65) == 4   # Acceptable range
    assert FactorScorer.score_rsi(75) == 2   # Overbought
    assert FactorScorer.score_rsi(85) == 1   # Extremely overbought
    assert FactorScorer.score_rsi(25) == 2   # Oversold
    assert FactorScorer.score_rsi(15) == 1   # Extremely oversold

def test_factor_scorer_valuation():
    # Test valuation scoring (PE vs sector)
    assert FactorScorer.score_valuation(15, 20) == 5  # Cheap vs sector
    assert FactorScorer.score_valuation(18, 20) == 4  # Slightly cheap
    assert FactorScorer.score_valuation(20, 20) == 3  # Fair value
    assert FactorScorer.score_valuation(25, 20) == 2  # Expensive
    assert FactorScorer.score_valuation(35, 20) == 1  # Very expensive

def test_factor_scorer_growth():
    # Test growth scoring
    assert FactorScorer.score_growth(0.20) == 5  # 20% growth
    assert FactorScorer.score_growth(0.12) == 4  # 12% growth
    assert FactorScorer.score_growth(0.07) == 3  # 7% growth
    assert FactorScorer.score_growth(0.02) == 2  # 2% growth
    assert FactorScorer.score_growth(-0.05) == 1 # Negative growth

def test_factor_scorer_quality():
    # Test quality scoring
    assert FactorScorer.score_quality(0.25, 0.18) == 5  # High ROE and ROIC
    assert FactorScorer.score_quality(0.18, 0.14) == 4  # Good ROE and ROIC
    assert FactorScorer.score_quality(0.12, 0.10) == 3  # Average ROE and ROIC
    assert FactorScorer.score_quality(0.08, 0.06) == 2  # Below average
    assert FactorScorer.score_quality(0.03, 0.02) == 1  # Poor quality

def test_technical_analyzer_indicators():
    # Create sample OHLCV data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100) * 0.02)
    
    df = pd.DataFrame({
        'open': prices * (1 + np.random.randn(100) * 0.01),
        'high': prices * (1 + np.abs(np.random.randn(100)) * 0.02),
        'low': prices * (1 - np.abs(np.random.randn(100)) * 0.02),
        'close': prices,
        'adj_close': prices,
        'volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    # Compute indicators
    result = TechnicalAnalyzer.compute_indicators(df)
    
    # Check that indicators were added
    assert 'ma50' in result.columns
    assert 'ma200' in result.columns
    assert 'rsi' in result.columns
    
    # Check that MA50 and MA200 are reasonable
    assert not result['ma50'].iloc[-1] != result['ma50'].iloc[-1]  # Not NaN
    # MA200 might be NaN for short series, that's OK

def test_pivot_levels():
    # Test support/resistance calculation
    prices = pd.Series([100, 105, 98, 102, 110, 95, 108, 103, 99, 106])
    support, resistance = TechnicalAnalyzer.pivot_levels(prices, lookback=10)
    
    assert support == 95.0  # Minimum
    assert resistance == 110.0  # Maximum

def test_data_provider_dummy_data():
    # Test that dummy data is generated when no API keys
    import asyncio
    
    async def test_fetch():
        df = await DataProvider.fetch_ohlcv("AAPL")
        assert not df.empty
        assert 'close' in df.columns
        assert len(df) == 252  # Should return 252 days
        
        fundamentals = await DataProvider.fetch_fundamentals("AAPL")
        assert 'metric' in fundamentals
        assert 'roe' in fundamentals['metric']
    
    asyncio.run(test_fetch())

def test_scoring_integration():
    # Test that all scoring functions handle edge cases
    
    # Test with NaN values
    assert FactorScorer.score_trend(100, float('nan'), 0.1) == 3
    assert FactorScorer.score_rsi(float('nan')) == 3
    assert FactorScorer.score_valuation(float('nan'), 20) == 3
    assert FactorScorer.score_growth(float('nan')) == 3
    assert FactorScorer.score_quality(float('nan'), float('nan')) == 3
    
    # Test boundary conditions
    assert FactorScorer.score_valuation(0, 20) == 3  # Zero PE
    assert FactorScorer.score_valuation(-5, 20) == 3  # Negative PE

if __name__ == "__main__":
    pytest.main([__file__])
