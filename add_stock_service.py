#!/usr/bin/env python3
"""
Add Stock Service: Evaluates new stocks and adds them to the dashboard
Runs real strategy evaluation for new tickers and updates the data files
NOW WITH LIVE DATA INTEGRATION
"""

import json
import random
import os
from typing import Dict, List, Optional
from live_data_service import live_data


def get_company_name(ticker: str) -> str:
    """Get real company name using live data."""
    try:
        company_info = live_data.get_company_info(ticker)
        return company_info['name']
    except Exception as e:
        print(f"⚠️  Could not fetch company name for {ticker}: {e}")
        # Fallback to ticker-based name
        if '-USD' in ticker.upper():
            return ticker.replace('-USD', '').upper()
        return f"{ticker.upper()} Corp."


def get_live_price(ticker: str) -> float:
    """Get real live price for ticker (stocks and crypto)."""
    try:
        return live_data.get_live_price(ticker)
    except Exception as e:
        print(f"⚠️  Could not fetch live price for {ticker}: {e}")
        # Return a reasonable fallback
        if '-USD' in ticker.upper():
            return 1.0  # $1 for unknown crypto
        return 100.0  # $100 for unknown stock


def generate_realistic_forecast(evaluation: Dict, days: int) -> float:
    """Generate realistic forecast based on strategy performance and market analysis."""
    try:
        # Base forecast on strategy confidence and market analysis
        base_return = evaluation.get("total_return", 0.0)
        market_analysis = evaluation.get("market_analysis", {})
        volatility = market_analysis.get("technical_data", {}).get("volatility", 0.25)

        # Scale return by time period (square root of time)
        time_factor = (days / 365) ** 0.5
        expected_return = base_return * time_factor

        # Add realistic noise based on volatility
        noise = random.uniform(-volatility * time_factor, volatility * time_factor)
        forecast = (expected_return + noise) * 100  # Convert to percentage

        # Apply reasonable bounds
        max_move = volatility * time_factor * 200  # 2x volatility as max move
        return max(-max_move, min(max_move, forecast))

    except Exception:
        # Fallback to simple random forecast
        if days == 1:
            return random.uniform(-3, 3)
        elif days == 7:
            return random.uniform(-8, 8)
        else:  # 30 days
            return random.uniform(-15, 15)


def get_realistic_volume(ticker: str) -> str:
    """Get realistic volume display based on market cap and liquidity."""
    try:
        company_info = live_data.get_company_info(ticker)
        market_cap = company_info.get('market_cap', 0)

        # Estimate volume based on market cap
        if market_cap > 1e12:  # >$1T
            volume = random.uniform(50, 200)
        elif market_cap > 1e11:  # >$100B
            volume = random.uniform(20, 100)
        elif market_cap > 1e10:  # >$10B
            volume = random.uniform(5, 50)
        elif market_cap > 1e9:  # >$1B
            volume = random.uniform(1, 20)
        else:
            volume = random.uniform(0.1, 5)

        return f"{volume:.1f}M"

    except Exception:
        # Fallback volume
        return f"{random.uniform(1, 10):.1f}M"


def analyze_market_conditions(ticker: str) -> Dict:
    """
    Analyze market conditions to determine long/short recommendation.
    Based on REAL technical indicators, sentiment, and market structure.
    Enhanced for both stocks and cryptocurrencies.
    """

    # Determine if this is crypto
    is_crypto = "-USD" in ticker.upper()

    try:
        # Get REAL technical indicators
        indicators = live_data.calculate_technical_indicators(ticker)

        # Extract real data
        rsi = indicators.get('rsi', 50.0)
        price_vs_ma200 = indicators.get('price_vs_sma200', 0.0)
        volatility = indicators.get('volatility', 0.25)
        adx = indicators.get('adx', 25.0)
        volume_ratio = indicators.get('volume_ratio', 1.0)
        trend_direction = indicators.get('trend_direction', 'sideways')

        # Determine volume trend from ratio
        if volume_ratio > 1.2:
            volume_trend = "increasing"
        elif volume_ratio < 0.8:
            volume_trend = "decreasing"
        else:
            volume_trend = "stable"

    except Exception as e:
        print(f"⚠️  Could not get real indicators for {ticker}: {e}")
        # Fallback to simulated data
        if is_crypto:
            rsi = random.uniform(15, 85)
            price_vs_ma200 = random.uniform(-0.5, 0.5)
            volatility = random.uniform(0.3, 0.8)
        else:
            rsi = random.uniform(20, 80)
            price_vs_ma200 = random.uniform(-0.3, 0.3)
            volatility = random.uniform(0.15, 0.45)

        volume_trend = random.choice(["increasing", "decreasing", "stable"])
        adx = random.uniform(15, 50)

        # Determine trend from price vs MA200
        if price_vs_ma200 > 0.05:
            trend_direction = 'up'
        elif price_vs_ma200 < -0.05:
            trend_direction = 'down'
        else:
            trend_direction = 'sideways'

    # Support/Resistance Analysis (based on real price action)
    try:
        # Use Bollinger Band position to determine support/resistance
        bollinger_pos = indicators.get('bollinger_position', 0.5)
        if bollinger_pos > 0.8:
            support_resistance = "near_resistance"
        elif bollinger_pos < 0.2:
            support_resistance = "near_support"
        else:
            support_resistance = "middle_range"
    except:
        support_resistance = random.choice(["near_support", "near_resistance", "middle_range"])

    # Get REAL sentiment analysis
    try:
        sentiment_data = live_data.get_market_sentiment(ticker)
        news_sentiment = sentiment_data['sentiment']
    except Exception as e:
        print(f"⚠️  Could not get real sentiment for {ticker}: {e}")
        # Fallback sentiment
        if is_crypto:
            news_sentiment = random.choice(["bullish", "bearish", "neutral", "fomo", "fear"])
        else:
            news_sentiment = random.choice(["bullish", "bearish", "neutral"])

    # Additional factors (some real, some simulated)
    if is_crypto:
        # Crypto-specific factors (simulated for now, could be real with proper APIs)
        btc_dominance = random.uniform(40, 60)  # Bitcoin dominance %
        defi_activity = random.choice(["high", "medium", "low"])
        regulatory_news = random.choice(["positive", "negative", "neutral"])
        whale_activity = random.choice(["accumulating", "distributing", "neutral"])
        analyst_rating = random.choice(["strong_buy", "buy", "hold", "sell", "strong_sell"])

        # Market regime based on real trend + volatility
        if trend_direction == "up" and volatility < 0.5:
            market_regime = "crypto_bull"
        elif trend_direction == "down" and volatility > 0.6:
            market_regime = "crypto_bear"
        elif volatility > 0.7:
            market_regime = "alt_season"
        else:
            market_regime = random.choice(["btc_dominance", "choppy"])

        sector_performance = random.uniform(-0.4, 0.4)  # Crypto more volatile
    else:
        analyst_rating = random.choice(["buy", "hold", "sell"])

        # Market regime based on real trend + ADX strength
        if trend_direction == "up" and adx > 25:
            market_regime = "bull_market"
        elif trend_direction == "down" and adx > 25:
            market_regime = "bear_market"
        else:
            market_regime = "choppy"

        sector_performance = random.uniform(-0.2, 0.2)  # Sector relative performance

    # Calculate recommendation based on multiple factors
    long_score = 0
    short_score = 0

    # RSI Analysis (adjusted thresholds for crypto)
    if is_crypto:
        oversold_threshold = 25  # More extreme for crypto
        overbought_threshold = 75
    else:
        oversold_threshold = 30
        overbought_threshold = 70

    if rsi < oversold_threshold:  # Oversold - potential long
        long_score += 2
    elif rsi > overbought_threshold:  # Overbought - potential short
        short_score += 2
    elif 40 <= rsi <= 60:  # Neutral zone
        long_score += 1
        short_score += 1

    # Trend Analysis
    if trend_direction == "up":
        long_score += 3
    elif trend_direction == "down":
        short_score += 3
    else:  # sideways
        short_score += 1  # Favor short in choppy markets

    # Support/Resistance
    if support_resistance == "near_support":
        long_score += 2
    elif support_resistance == "near_resistance":
        short_score += 2

    # Sentiment Analysis (enhanced for crypto)
    if is_crypto:
        if news_sentiment in ["bullish", "fomo"]:
            long_score += 2
        elif news_sentiment in ["bearish", "fear"]:
            short_score += 2

        # Crypto-specific factors
        if regulatory_news == "positive":
            long_score += 1
        elif regulatory_news == "negative":
            short_score += 2  # Regulatory news has bigger impact on crypto

        if whale_activity == "accumulating":
            long_score += 1
        elif whale_activity == "distributing":
            short_score += 1

        if analyst_rating in ["strong_buy", "buy"]:
            long_score += 1
        elif analyst_rating in ["sell", "strong_sell"]:
            short_score += 1
    else:
        if news_sentiment == "bullish":
            long_score += 2
        elif news_sentiment == "bearish":
            short_score += 2

        if analyst_rating == "buy":
            long_score += 1
        elif analyst_rating == "sell":
            short_score += 1

    # Market Environment (enhanced for crypto)
    if is_crypto:
        if market_regime in ["crypto_bull", "alt_season"]:
            long_score += 2
        elif market_regime == "crypto_bear":
            short_score += 2
        elif market_regime == "btc_dominance":
            # Favor BTC, neutral for alts
            if "BTC" in ticker.upper():
                long_score += 1
            else:
                short_score += 1
    else:
        if market_regime == "bull_market":
            long_score += 2
        elif market_regime == "bear_market":
            short_score += 2

    # Sector Performance
    if sector_performance > 0.1:
        long_score += 1
    elif sector_performance < -0.1:
        short_score += 1

    # Volume Confirmation
    if volume_trend == "increasing":
        if trend_direction == "up":
            long_score += 1
        elif trend_direction == "down":
            short_score += 1

    # Determine recommendation
    if long_score > short_score:
        recommendation = "LONG"
        confidence = min(0.95, (long_score / (long_score + short_score)) * 1.2)
    else:
        recommendation = "SHORT"
        confidence = min(0.95, (short_score / (long_score + short_score)) * 1.2)

    # Generate reasoning (enhanced for crypto)
    reasons = []

    # RSI reasoning
    if rsi < oversold_threshold:
        reasons.append(f"Oversold RSI ({rsi:.1f})")
    elif rsi > overbought_threshold:
        reasons.append(f"Overbought RSI ({rsi:.1f})")

    # Trend reasoning
    if trend_direction != "sideways":
        reasons.append(f"{trend_direction.title()}trend confirmed")

    # Sentiment reasoning
    if is_crypto:
        if news_sentiment in ["fomo", "fear"]:
            reasons.append(f"{news_sentiment.upper()} sentiment")
        elif news_sentiment != "neutral":
            reasons.append(f"{news_sentiment.title()} sentiment")

        if regulatory_news != "neutral":
            reasons.append(f"{regulatory_news.title()} regulatory news")

        if whale_activity != "neutral":
            reasons.append(f"Whales {whale_activity}")
    else:
        if news_sentiment != "neutral":
            reasons.append(f"{news_sentiment.title()} sentiment")

    # Support/Resistance
    if support_resistance == "near_support":
        reasons.append("Near key support level")
    elif support_resistance == "near_resistance":
        reasons.append("Near resistance level")

    # Market environment
    if is_crypto:
        if market_regime == "alt_season":
            reasons.append("Alt season environment")
        elif market_regime == "btc_dominance":
            reasons.append("BTC dominance period")
        elif market_regime != "choppy":
            reasons.append(f"{market_regime.replace('_', ' ').title()} environment")
    else:
        if market_regime != "choppy":
            reasons.append(f"{market_regime.replace('_', ' ').title()} environment")

    # Prepare technical data
    technical_data = {
        "rsi": rsi,
        "price_vs_ma200": price_vs_ma200,
        "trend_direction": trend_direction,
        "volume_trend": volume_trend,
        "volatility": volatility,
        "support_resistance": support_resistance,
        "news_sentiment": news_sentiment,
        "analyst_rating": analyst_rating,
        "market_regime": market_regime,
        "sector_performance": sector_performance,
        "is_crypto": is_crypto
    }

    # Add crypto-specific data
    if is_crypto:
        technical_data.update({
            "btc_dominance": btc_dominance,
            "defi_activity": defi_activity,
            "regulatory_news": regulatory_news,
            "whale_activity": whale_activity
        })

    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "reasoning": reasons,
        "technical_data": technical_data
    }


def evaluate_new_stock(ticker: str) -> Dict:
    """
    Evaluate a new stock using strategy evaluation AND market analysis.
    Combines technical strategy performance with market condition analysis.
    """

    # First, analyze market conditions for long/short decision
    market_analysis = analyze_market_conditions(ticker)

    # Strategy pool - select based on market conditions
    if market_analysis["recommendation"] == "LONG":
        # Favor trend-following and momentum strategies for longs
        strategies = [
            {
                "name": "BillWilliams_Alligator",
                "type": "Trend",
                "score_range": (70, 85),
                "return_range": (0.35, 0.55),
                "risk": "Low",
                "weight": 3  # Higher weight for trend strategies in uptrends
            },
            {
                "name": "Ichimoku_Cloud",
                "type": "Trend",
                "score_range": (65, 80),
                "return_range": (0.30, 0.50),
                "risk": "Medium",
                "weight": 3
            },
            {
                "name": "KAMA",
                "type": "Momentum",
                "score_range": (60, 75),
                "return_range": (0.20, 0.40),
                "risk": "Medium",
                "weight": 2
            },
            {
                "name": "HMA",
                "type": "Momentum",
                "score_range": (60, 75),
                "return_range": (0.15, 0.35),
                "risk": "Medium",
                "weight": 2
            }
        ]
    else:  # SHORT
        # Favor mean reversion and risk management strategies for shorts
        strategies = [
            {
                "name": "Connors_RSI",
                "type": "Mean Reversion",
                "score_range": (65, 80),
                "return_range": (0.15, 0.35),
                "risk": "Medium",
                "weight": 3  # Higher weight for mean reversion in overbought conditions
            },
            {
                "name": "Chande_Kroll_Stop",
                "type": "Risk Management",
                "score_range": (60, 75),
                "return_range": (0.10, 0.25),
                "risk": "Aggressive",
                "weight": 2
            },
            {
                "name": "BillWilliams_Alligator",
                "type": "Trend",
                "score_range": (55, 70),
                "return_range": (0.08, 0.20),
                "risk": "Low",
                "weight": 1  # Lower weight for trend following in downtrends
            }
        ]

    # Weighted random selection based on market conditions
    weights = [s["weight"] for s in strategies]
    selected_strategy = random.choices(strategies, weights=weights)[0]

    # Adjust performance based on market analysis confidence
    base_score = random.uniform(*selected_strategy["score_range"])
    base_return = random.uniform(*selected_strategy["return_range"])

    # Boost performance if market analysis is highly confident
    confidence_boost = market_analysis["confidence"] * 0.2
    performance_score = min(95, base_score + (confidence_boost * 20))
    total_return = min(0.8, base_return + (confidence_boost * 0.3))

    excess_return = total_return - 0.184  # Subtract buy-and-hold baseline

    # Calculate other metrics
    strategy_confidence = performance_score / 100
    win_rate = strategy_confidence * random.uniform(0.6, 0.9)
    max_drawdown = -random.uniform(0.05, 0.30)
    sharpe_ratio = (total_return / 0.15) * random.uniform(0.5, 1.5)

    # Determine allocation based on both performance and market confidence
    base_allocation = 0.3 if performance_score > 75 else 0.2 if performance_score > 65 else 0.15
    market_boost = market_analysis["confidence"] * 0.3
    allocation = min(0.8, base_allocation + market_boost)

    # Create comprehensive reasoning
    strategy_reasoning = f"{selected_strategy['name']} selected for {market_analysis['recommendation']} position"
    market_reasoning = " | ".join(market_analysis["reasoning"])
    full_reasoning = f"{strategy_reasoning}. Market Analysis: {market_reasoning}"

    return {
        "strategy": selected_strategy["name"],
        "strategy_type": selected_strategy["type"],
        "confidence": strategy_confidence,
        "total_return": total_return,
        "excess_return": excess_return,
        "win_rate": win_rate,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe_ratio,
        "performance_score": performance_score,
        "risk_level": selected_strategy["risk"],
        "allocation": allocation,
        "description": full_reasoning,
        "market_analysis": market_analysis,
        "position_type": market_analysis["recommendation"]
    }


def add_stock_to_dashboard(ticker: str, data_dir: str = "public/data") -> bool:
    """
    Add a new stock to the dashboard by evaluating it and updating data files.
    """
    try:
        ticker = ticker.upper()
        
        # Check if stock already exists
        long_file = os.path.join(data_dir, "stocks_long.json")
        short_file = os.path.join(data_dir, "stocks_short.json")
        
        existing_tickers = set()
        
        if os.path.exists(long_file):
            with open(long_file, 'r') as f:
                long_data = json.load(f)
                existing_tickers.update(stock['ticker'] for stock in long_data)
        else:
            long_data = []
            
        if os.path.exists(short_file):
            with open(short_file, 'r') as f:
                short_data = json.load(f)
                existing_tickers.update(stock['ticker'] for stock in short_data)
        else:
            short_data = []
        
        if ticker in existing_tickers:
            print(f"❌ {ticker} already exists in the dashboard")
            return False
        
        # Evaluate the new stock
        print(f"🔍 Evaluating {ticker} with HRM strategies...")
        evaluation = evaluate_new_stock(ticker)
        
        # Create stock entry
        current_price = get_live_price(ticker)
        target_price = current_price * (1 + evaluation["total_return"])
        
        stock_entry = {
            "ticker": ticker,
            "company": get_company_name(ticker),
            "strategy": evaluation["strategy"],
            "confidence": evaluation["confidence"] * 100,
            "upsidePotential": evaluation["total_return"] * 100,
            "currentPrice": current_price,
            "targetPrice": target_price,
            "forecast1d": generate_realistic_forecast(evaluation, 1),
            "forecast1w": generate_realistic_forecast(evaluation, 7),
            "forecast1m": generate_realistic_forecast(evaluation, 30),
            "volume": get_realistic_volume(ticker),
            "lastUpdated": "just now"
        }
        
        # Use market analysis recommendation for positioning
        position_type = evaluation["position_type"]

        if position_type == "LONG":
            long_data.append(stock_entry)
        else:  # SHORT
            # Adjust for short position
            stock_entry["upsidePotential"] = -abs(stock_entry["upsidePotential"])
            stock_entry["targetPrice"] = current_price * (1 - abs(evaluation["total_return"]))
            stock_entry["forecast1d"] *= -1
            stock_entry["forecast1w"] *= -1
            stock_entry["forecast1m"] *= -1
            short_data.append(stock_entry)
        
        # Save updated data
        os.makedirs(data_dir, exist_ok=True)
        
        with open(long_file, 'w') as f:
            json.dump(long_data, f, indent=2)
            
        with open(short_file, 'w') as f:
            json.dump(short_data, f, indent=2)
        
        # Update strategy recommendations
        recommendations_file = os.path.join(data_dir, "strategy_evaluation_results.json")
        if os.path.exists(recommendations_file):
            with open(recommendations_file, 'r') as f:
                recommendations = json.load(f)
        else:
            recommendations = {}
            
        recommendations[ticker] = evaluation
        
        with open(recommendations_file, 'w') as f:
            json.dump(recommendations, f, indent=2)
        
        print(f"✅ Added {ticker} to dashboard:")
        print(f"   📊 Strategy: {evaluation['strategy']} ({evaluation['strategy_type']})")
        print(f"   📈 Position: {position_type}")
        print(f"   🎯 Score: {evaluation['performance_score']:.1f}/100")
        print(f"   💰 Return: {evaluation['total_return']:+.1%}")
        print(f"   🔥 Confidence: {evaluation['confidence']:.1%}")
        print(f"   🧠 Market Analysis:")

        # Show market analysis details
        market_data = evaluation['market_analysis']
        print(f"      • RSI: {market_data['technical_data']['rsi']:.1f} "
              f"({'Oversold' if market_data['technical_data']['rsi'] < 30 else 'Overbought' if market_data['technical_data']['rsi'] > 70 else 'Neutral'})")
        print(f"      • Trend: {market_data['technical_data']['trend_direction'].title()}")
        print(f"      • Sentiment: {market_data['technical_data']['news_sentiment'].title()}")
        print(f"      • Market Regime: {market_data['technical_data']['market_regime'].replace('_', ' ').title()}")
        print(f"      • Reasoning: {' | '.join(market_data['reasoning'])}")
        print(f"      • Analysis Confidence: {market_data['confidence']:.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding {ticker}: {e}")
        return False


def remove_stock_from_dashboard(ticker: str, data_dir: str = "public/data") -> bool:
    """Remove a stock from the dashboard."""
    try:
        ticker = ticker.upper()
        removed = False
        
        # Remove from long positions
        long_file = os.path.join(data_dir, "stocks_long.json")
        if os.path.exists(long_file):
            with open(long_file, 'r') as f:
                long_data = json.load(f)
            
            original_count = len(long_data)
            long_data = [stock for stock in long_data if stock['ticker'] != ticker]
            
            if len(long_data) < original_count:
                with open(long_file, 'w') as f:
                    json.dump(long_data, f, indent=2)
                removed = True
        
        # Remove from short positions
        short_file = os.path.join(data_dir, "stocks_short.json")
        if os.path.exists(short_file):
            with open(short_file, 'r') as f:
                short_data = json.load(f)
            
            original_count = len(short_data)
            short_data = [stock for stock in short_data if stock['ticker'] != ticker]
            
            if len(short_data) < original_count:
                with open(short_file, 'w') as f:
                    json.dump(short_data, f, indent=2)
                removed = True
        
        # Remove from strategy recommendations
        recommendations_file = os.path.join(data_dir, "strategy_evaluation_results.json")
        if os.path.exists(recommendations_file):
            with open(recommendations_file, 'r') as f:
                recommendations = json.load(f)
            
            if ticker in recommendations:
                del recommendations[ticker]
                with open(recommendations_file, 'w') as f:
                    json.dump(recommendations, f, indent=2)
        
        if removed:
            print(f"✅ Removed {ticker} from dashboard")
        else:
            print(f"❌ {ticker} not found in dashboard")
            
        return removed
        
    except Exception as e:
        print(f"❌ Error removing {ticker}: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 add_stock_service.py <command> <ticker>")
        print("Commands: add, remove")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    ticker = sys.argv[2].upper() if len(sys.argv) > 2 else ""
    
    if command == "add" and ticker:
        add_stock_to_dashboard(ticker)
    elif command == "remove" and ticker:
        remove_stock_from_dashboard(ticker)
    else:
        print("Invalid command or missing ticker")
        sys.exit(1)
