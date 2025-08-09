from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import httpx
import pandas as pd
# import pandas_ta as ta  # Optional dependency
import numpy as np
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

app = FastAPI(title="Stock Analysis Assistant")

# Serve static files if they exist
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")

class DataProvider:
    @staticmethod
    async def fetch_ohlcv(symbol: str) -> pd.DataFrame:
        """Fetch OHLCV data from Alpha Vantage"""
        if not ALPHAVANTAGE_API_KEY:
            # Return dummy data for demo
            dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
            np.random.seed(42)
            price = 100 + np.cumsum(np.random.randn(252) * 0.02)
            return pd.DataFrame({
                'date': dates,
                'open': price * (1 + np.random.randn(252) * 0.01),
                'high': price * (1 + np.abs(np.random.randn(252)) * 0.02),
                'low': price * (1 - np.abs(np.random.randn(252)) * 0.02),
                'close': price,
                'volume': np.random.randint(1000000, 10000000, 252)
            }).set_index('date')
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": "full",
            "apikey": ALPHAVANTAGE_API_KEY
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            
        if "Time Series (Daily)" not in data:
            raise HTTPException(400, f"No data for {symbol}")
            
        ts = data["Time Series (Daily)"]
        df = pd.DataFrame.from_dict(ts, orient="index")
        df.columns = [col.split(". ")[1] for col in df.columns]
        df = df.rename(columns={"adjusted close": "adj_close"})
        df.index = pd.to_datetime(df.index)
        df = df.astype(float).sort_index()
        
        # Keep last 400 days
        cutoff = datetime.now() - timedelta(days=400)
        return df[df.index >= cutoff]

    @staticmethod
    async def fetch_fundamentals(symbol: str) -> Dict[str, Any]:
        """Fetch fundamentals from Finnhub"""
        if not FINNHUB_API_KEY:
            # Return dummy data
            return {
                "metric": {
                    "roe": 0.15,
                    "roic": 0.12,
                    "peBasicExclExtraTTM": 25.5,
                    "psTTM": 8.2,
                    "evToEbitda": 18.3,
                    "revenueCagr3Y": 0.08,
                    "epsGrowth3Y": 0.12,
                    "totalDebt/totalEquityAnnual": 0.45,
                    "freeCashFlowTTM": 50000000000
                }
            }
        
        url = "https://finnhub.io/api/v1/stock/metric"
        params = {"symbol": symbol, "metric": "all", "token": FINNHUB_API_KEY}
        
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()

class TechnicalAnalyzer:
    @staticmethod
    def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Compute technical indicators using simple pandas operations"""
        close = df["adj_close"] if "adj_close" in df.columns else df["close"]

        # Moving averages
        df["ma50"] = close.rolling(window=50).mean()
        df["ma200"] = close.rolling(window=200).mean()

        # Simple RSI calculation
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        # Simple MACD
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        df["MACD"] = ema12 - ema26
        df["MACD_signal"] = df["MACD"].ewm(span=9).mean()
        df["MACD_histogram"] = df["MACD"] - df["MACD_signal"]

        # Volume average
        if "volume" in df.columns:
            df["vol_avg_20"] = df["volume"].rolling(window=20).mean()

        return df

    @staticmethod
    def pivot_levels(close: pd.Series, lookback: int = 50) -> tuple:
        """Calculate support and resistance levels"""
        if len(close) < lookback:
            return float(close.min()), float(close.max())
        
        recent = close.tail(lookback)
        support = float(recent.min())
        resistance = float(recent.max())
        return support, resistance

class FactorScorer:
    @staticmethod
    def score_trend(price: float, ma200: float, ma200_slope: float) -> int:
        """Score long-term trend (1-5)"""
        if pd.isna(ma200) or pd.isna(ma200_slope):
            return 3
        if price > ma200 and ma200_slope > 0:
            return 5
        if price > ma200:
            return 4
        if abs(ma200_slope) < 1e-6:
            return 3
        return 1

    @staticmethod
    def score_rsi(rsi: float) -> int:
        """Score RSI positioning (1-5)"""
        if pd.isna(rsi):
            return 3
        if 40 <= rsi <= 60:
            return 5
        if 30 <= rsi <= 70:
            return 4
        if 20 <= rsi < 30 or 70 < rsi <= 80:
            return 2
        return 1

    @staticmethod
    def score_valuation(pe: float, sector_pe: float = 20.0) -> int:
        """Score valuation relative to sector (1-5)"""
        if pd.isna(pe) or pe <= 0:
            return 3
        
        z = (pe - sector_pe) / max(1.0, sector_pe * 0.5)
        if z <= -0.5:
            return 5
        elif z <= -0.2:
            return 4
        elif abs(z) < 0.2:
            return 3
        elif z <= 0.5:
            return 2
        else:
            return 1

    @staticmethod
    def score_growth(growth_rate: float) -> int:
        """Score growth rate (1-5)"""
        if pd.isna(growth_rate):
            return 3
        if growth_rate >= 0.15:
            return 5
        elif growth_rate >= 0.10:
            return 4
        elif growth_rate >= 0.05:
            return 3
        elif growth_rate >= 0:
            return 2
        else:
            return 1

    @staticmethod
    def score_quality(roe: float, roic: float) -> int:
        """Score quality metrics (1-5)"""
        if pd.isna(roe) and pd.isna(roic):
            return 3
        
        roe_score = 0
        if not pd.isna(roe):
            if roe >= 0.20:
                roe_score = 5
            elif roe >= 0.15:
                roe_score = 4
            elif roe >= 0.10:
                roe_score = 3
            elif roe >= 0.05:
                roe_score = 2
            else:
                roe_score = 1
        
        roic_score = 0
        if not pd.isna(roic):
            if roic >= 0.15:
                roic_score = 5
            elif roic >= 0.12:
                roic_score = 4
            elif roic >= 0.08:
                roic_score = 3
            elif roic >= 0.05:
                roic_score = 2
            else:
                roic_score = 1
        
        if roe_score > 0 and roic_score > 0:
            return int((roe_score + roic_score) / 2)
        elif roe_score > 0:
            return roe_score
        elif roic_score > 0:
            return roic_score
        else:
            return 3

@app.get("/", response_class=HTMLResponse)
async def home():
    """Simple HTML interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Stock Analysis Assistant</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .form-group { margin: 20px 0; }
            input[type="text"] { padding: 10px; font-size: 16px; width: 200px; }
            button { padding: 10px 20px; font-size: 16px; background: #007cba; color: white; border: none; cursor: pointer; }
            .result { margin-top: 20px; padding: 20px; background: #f5f5f5; border-radius: 5px; }
            .score { font-weight: bold; color: #007cba; }
        </style>
    </head>
    <body>
        <h1>Stock Analysis Assistant</h1>
        <div class="form-group">
            <input type="text" id="ticker" placeholder="Enter ticker (e.g., AAPL)" />
            <button onclick="analyze()">Analyze</button>
        </div>
        <div id="result"></div>
        
        <script>
            async function analyze() {
                const ticker = document.getElementById('ticker').value.toUpperCase();
                if (!ticker) return;
                
                document.getElementById('result').innerHTML = 'Analyzing...';
                
                try {
                    const response = await fetch(`/analyze?ticker=${ticker}`);
                    const data = await response.json();
                    
                    if (response.ok) {
                        displayResult(data);
                    } else {
                        document.getElementById('result').innerHTML = `Error: ${data.detail}`;
                    }
                } catch (error) {
                    document.getElementById('result').innerHTML = `Error: ${error.message}`;
                }
            }
            
            function displayResult(data) {
                const html = `
                    <div class="result">
                        <h2>${data.symbol} Analysis</h2>
                        <p><strong>Price:</strong> $${data.price.toFixed(2)}</p>
                        <p><strong>Decision:</strong> <span class="score">${data.decision}</span></p>
                        <p><strong>Total Score:</strong> ${data.total_score.toFixed(1)}/${data.max_score} (${(data.score_percentage*100).toFixed(1)}%)</p>
                        
                        <h3>Traditional Factor Scores</h3>
                        <ul>
                            <li>Long-term Trend: ${data.traditional_scores.long_term_trend.toFixed(1)}/5</li>
                            <li>RSI Position: ${data.traditional_scores.rsi_position.toFixed(1)}/5</li>
                            <li>Valuation: ${data.traditional_scores.valuation.toFixed(1)}/5</li>
                            <li>Growth: ${data.traditional_scores.growth.toFixed(1)}/5</li>
                            <li>Quality: ${data.traditional_scores.quality.toFixed(1)}/5</li>
                        </ul>

                        <h3>Macro & Sentiment Scores</h3>
                        <ul>
                            <li>Macro Regime: ${data.macro_scores.macro_regime.toFixed(1)}/5</li>
                            <li>Market Risk: ${data.macro_scores.market_risk.toFixed(1)}/5</li>
                            <li>Sentiment: ${data.macro_scores.sentiment.toFixed(1)}/5</li>
                        </ul>
                        
                        <h3>Technical Indicators</h3>
                        <ul>
                            <li>MA50: $${data.technicals.ma50.toFixed(2)}</li>
                            <li>MA200: $${data.technicals.ma200.toFixed(2)}</li>
                            <li>RSI: ${data.technicals.rsi.toFixed(1)}</li>
                            <li>Support: $${data.technicals.support.toFixed(2)}</li>
                            <li>Resistance: $${data.technicals.resistance.toFixed(2)}</li>
                        </ul>
                    </div>
                `;
                document.getElementById('result').innerHTML = html;
            }
            
            // Allow Enter key to trigger analysis
            document.getElementById('ticker').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') analyze();
            });
        </script>
    </body>
    </html>
    """

async def fetch_macro_sentiment_scores(ticker: str) -> Dict[str, Any]:
    """Fetch macro and sentiment scores from the macro_sentiment_api"""
    macro_sentiment_base = "http://127.0.0.1:8001"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Fetch macro score
            macro_resp = await client.get(f"{macro_sentiment_base}/scoring/macro")
            macro_data = macro_resp.json() if macro_resp.status_code == 200 else {"score": 5}

            # Fetch market risk score
            risk_resp = await client.get(f"{macro_sentiment_base}/scoring/market_risk")
            risk_data = risk_resp.json() if risk_resp.status_code == 200 else {"score": 5}

            # Fetch sentiment score
            sentiment_resp = await client.get(f"{macro_sentiment_base}/scoring/sentiment/{ticker}")
            sentiment_data = sentiment_resp.json() if sentiment_resp.status_code == 200 else {"score": 5}

            return {
                "macro_score": macro_data.get("score", 5),
                "market_risk_score": risk_data.get("score", 5),
                "sentiment_score": sentiment_data.get("score", 5),
                "macro_details": macro_data,
                "risk_details": risk_data,
                "sentiment_details": sentiment_data
            }
    except Exception:
        # Return neutral scores if macro service unavailable
        return {
            "macro_score": 5,
            "market_risk_score": 5,
            "sentiment_score": 5,
            "macro_details": {"score": 5, "error": "Service unavailable"},
            "risk_details": {"score": 5, "error": "Service unavailable"},
            "sentiment_details": {"score": 5, "error": "Service unavailable"}
        }

@app.get("/analyze")
async def analyze_stock(ticker: str = Query(..., description="Stock ticker symbol")):
    """Analyze a stock and return scores and recommendation"""
    try:
        # Fetch data in parallel
        ohlcv_task = DataProvider.fetch_ohlcv(ticker)
        fundamentals_task = DataProvider.fetch_fundamentals(ticker)
        macro_sentiment_task = fetch_macro_sentiment_scores(ticker)

        ohlcv, fundamentals, macro_sentiment = await asyncio.gather(
            ohlcv_task, fundamentals_task, macro_sentiment_task
        )

        # Compute technical indicators
        df = TechnicalAnalyzer.compute_indicators(ohlcv)
        
        # Extract latest values
        latest = df.iloc[-1]
        price = float(latest["adj_close"] if "adj_close" in latest else latest["close"])
        ma50 = float(latest["ma50"]) if not pd.isna(latest["ma50"]) else price
        ma200 = float(latest["ma200"]) if not pd.isna(latest["ma200"]) else price
        rsi = float(latest["rsi"]) if not pd.isna(latest["rsi"]) else 50.0
        
        # Calculate MA200 slope
        ma200_series = df["ma200"].dropna()
        if len(ma200_series) >= 30:
            ma200_slope = float(np.polyfit(range(30), ma200_series.tail(30), 1)[0])
        else:
            ma200_slope = 0.0
        
        # Support/resistance
        close_series = df["adj_close"] if "adj_close" in df.columns else df["close"]
        support, resistance = TechnicalAnalyzer.pivot_levels(close_series)
        
        # Extract fundamental metrics
        metrics = fundamentals.get("metric", {})
        roe = metrics.get("roe")
        roic = metrics.get("roic")
        pe = metrics.get("peBasicExclExtraTTM")
        rev_growth = metrics.get("revenueCagr3Y")
        
        # Score factors (traditional 1-5 scale)
        traditional_scores = {
            "long_term_trend": FactorScorer.score_trend(price, ma200, ma200_slope),
            "rsi_position": FactorScorer.score_rsi(rsi),
            "valuation": FactorScorer.score_valuation(pe),
            "growth": FactorScorer.score_growth(rev_growth),
            "quality": FactorScorer.score_quality(roe, roic)
        }

        # Add macro/sentiment scores (0-10 scale, normalize to 0-5)
        macro_scores = {
            "macro_regime": macro_sentiment["macro_score"] / 2,  # 0-10 -> 0-5
            "market_risk": macro_sentiment["market_risk_score"] / 2,  # 0-10 -> 0-5
            "sentiment": macro_sentiment["sentiment_score"] / 2  # 0-10 -> 0-5
        }

        # Combine all scores
        all_scores = {**traditional_scores, **macro_scores}
        total_score = sum(all_scores.values())
        max_possible = len(all_scores) * 5  # 8 factors * 5 points = 40

        # Decision logic (adjusted for expanded scoring)
        score_percentage = total_score / max_possible
        if score_percentage >= 0.65:  # 65% or higher
            decision = "Buy"
        elif score_percentage >= 0.45:  # 45-64%
            decision = "Hold"
        else:
            decision = "Avoid"
        
        return {
            "symbol": ticker.upper(),
            "price": price,
            "decision": decision,
            "total_score": total_score,
            "max_score": max_possible,
            "score_percentage": score_percentage,
            "scores": all_scores,
            "traditional_scores": traditional_scores,
            "macro_scores": macro_scores,
            "technicals": {
                "ma50": ma50,
                "ma200": ma200,
                "rsi": rsi,
                "support": support,
                "resistance": resistance
            },
            "fundamentals": {
                "roe": roe,
                "roic": roic,
                "pe": pe,
                "revenue_growth_3y": rev_growth
            }
        }
        
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "stock_analyzer"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
