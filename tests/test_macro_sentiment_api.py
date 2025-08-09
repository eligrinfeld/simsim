import pytest
import sys
import os
from datetime import date

# Add the macro sentiment API to the path
macro_api_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'macro_sentiment_api')
sys.path.insert(0, macro_api_path)

# Import from the macro sentiment API
import importlib.util
spec = importlib.util.spec_from_file_location("macro_app", os.path.join(macro_api_path, "app.py"))
macro_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(macro_app)

MacroSnapshot = macro_app.MacroSnapshot
score_macro_regime = macro_app.score_macro_regime
score_market_risk = macro_app.score_market_risk
score_sentiment = macro_app.score_sentiment

def test_macro_snapshot_creation():
    # Test MacroSnapshot dataclass
    snapshot = MacroSnapshot(
        as_of_date=date.today(),
        inflation_yoy=0.025,
        unemployment_rate=0.045,
        policy_rate=0.05,
        yc_10y_2y=0.01,
        recession_proxy=False
    )
    
    assert snapshot.inflation_yoy == 0.025
    assert snapshot.unemployment_rate == 0.045
    assert not snapshot.recession_proxy

def test_score_macro_regime():
    # Test macro regime scoring
    
    # Good macro conditions
    good_snapshot = MacroSnapshot(
        as_of_date=date.today(),
        inflation_yoy=0.02,  # Low inflation
        unemployment_rate=0.04,  # Low unemployment
        yc_10y_2y=0.02,  # Normal yield curve
        recession_proxy=False
    )
    score = score_macro_regime(good_snapshot)
    assert score >= 7  # Should get high score
    
    # Bad macro conditions
    bad_snapshot = MacroSnapshot(
        as_of_date=date.today(),
        inflation_yoy=0.08,  # High inflation
        unemployment_rate=0.08,  # High unemployment
        yc_10y_2y=-0.02,  # Inverted yield curve
        recession_proxy=True
    )
    score = score_macro_regime(bad_snapshot)
    assert score <= 3  # Should get low score
    
    # Neutral conditions
    neutral_snapshot = MacroSnapshot(
        as_of_date=date.today(),
        inflation_yoy=0.04,  # Moderate inflation
        unemployment_rate=0.06,  # Moderate unemployment
        yc_10y_2y=0.005,  # Slightly positive yield curve
        recession_proxy=False
    )
    score = score_macro_regime(neutral_snapshot)
    assert 3 <= score <= 7  # Should get moderate score

def test_score_market_risk():
    # Test market risk scoring
    
    # Low risk conditions
    low_risk_score = score_market_risk(
        vix_percentile=0.2,  # Low VIX
        put_call_ratio=0.8,  # More calls than puts
        breadth_pct=0.7  # Good breadth
    )
    assert low_risk_score >= 6
    
    # High risk conditions
    high_risk_score = score_market_risk(
        vix_percentile=0.9,  # High VIX
        put_call_ratio=1.3,  # More puts than calls
        breadth_pct=0.2  # Poor breadth
    )
    assert high_risk_score <= 4
    
    # Moderate risk conditions
    moderate_risk_score = score_market_risk(
        vix_percentile=0.5,  # Moderate VIX
        put_call_ratio=1.0,  # Balanced put/call
        breadth_pct=0.5  # Moderate breadth
    )
    assert 2 <= moderate_risk_score <= 6

def test_score_sentiment():
    # Test sentiment scoring
    
    # Positive sentiment, no geopolitical risk
    positive_score = score_sentiment(avg_score=0.5, geopolitics_flag=False)
    assert positive_score >= 7
    
    # Negative sentiment, no geopolitical risk
    negative_score = score_sentiment(avg_score=-0.5, geopolitics_flag=False)
    assert negative_score <= 3
    
    # Positive sentiment with geopolitical risk
    geo_risk_score = score_sentiment(avg_score=0.5, geopolitics_flag=True)
    assert geo_risk_score < positive_score  # Should be lower due to geo risk
    
    # Neutral sentiment
    neutral_score = score_sentiment(avg_score=0.0, geopolitics_flag=False)
    assert 4 <= neutral_score <= 6

def test_scoring_bounds():
    # Test that all scoring functions return values in expected ranges
    
    # Macro regime scoring (0-10)
    for inflation in [0.01, 0.05, 0.10]:
        for unemployment in [0.03, 0.06, 0.10]:
            for yc_spread in [-0.02, 0.0, 0.02]:
                for recession in [True, False]:
                    snapshot = MacroSnapshot(
                        as_of_date=date.today(),
                        inflation_yoy=inflation,
                        unemployment_rate=unemployment,
                        yc_10y_2y=yc_spread,
                        recession_proxy=recession
                    )
                    score = score_macro_regime(snapshot)
                    assert 0 <= score <= 10
    
    # Market risk scoring (0-10)
    for vix_pct in [0.1, 0.5, 0.9]:
        for put_call in [0.7, 1.0, 1.3]:
            for breadth in [0.2, 0.5, 0.8]:
                score = score_market_risk(vix_pct, put_call, breadth)
                assert 0 <= score <= 10
    
    # Sentiment scoring (0-10)
    for sentiment in [-0.8, 0.0, 0.8]:
        for geo_flag in [True, False]:
            score = score_sentiment(sentiment, geo_flag)
            assert 0 <= score <= 10

def test_edge_cases():
    # Test edge cases and None values
    
    # Macro snapshot with None values
    sparse_snapshot = MacroSnapshot(
        as_of_date=date.today(),
        inflation_yoy=None,
        unemployment_rate=None,
        yc_10y_2y=None,
        recession_proxy=False
    )
    score = score_macro_regime(sparse_snapshot)
    assert 0 <= score <= 10  # Should handle None values gracefully
    
    # Extreme values
    extreme_snapshot = MacroSnapshot(
        as_of_date=date.today(),
        inflation_yoy=0.5,  # 50% inflation
        unemployment_rate=0.25,  # 25% unemployment
        yc_10y_2y=-0.1,  # Deeply inverted
        recession_proxy=True
    )
    score = score_macro_regime(extreme_snapshot)
    assert score == 0  # Should get minimum score

if __name__ == "__main__":
    pytest.main([__file__])
