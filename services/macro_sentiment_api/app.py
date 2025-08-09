from fastapi import FastAPI, HTTPException, Depends
from typing import Optional, Dict, Any, List
import os
import httpx
import pandas as pd
from datetime import datetime, date, timedelta
import json
import asyncio
from dataclasses import dataclass

app = FastAPI(title="Macro Sentiment API")

# Configuration
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
GDELT_BASE = os.getenv("GDELT_BASE", "https://data.gdeltproject.org/gdeltv2")

@dataclass
class MacroSnapshot:
    as_of_date: date
    inflation_yoy: Optional[float] = None
    core_inflation_yoy: Optional[float] = None
    unemployment_rate: Optional[float] = None
    policy_rate: Optional[float] = None
    yc_10y_2y: Optional[float] = None
    recession_proxy: bool = False

class FREDClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"
    
    async def fetch_series(self, series_id: str, limit: int = 100) -> pd.DataFrame:
        """Fetch FRED time series data"""
        if not self.api_key:
            # Return dummy data for demo
            dates = pd.date_range(end=datetime.now(), periods=limit, freq='D')
            if series_id == "CPIAUCSL":
                values = [300 + i * 0.1 for i in range(limit)]
            elif series_id == "UNRATE":
                values = [4.0 + (i % 10) * 0.1 for i in range(limit)]
            elif series_id == "FEDFUNDS":
                values = [5.0 + (i % 20) * 0.05 for i in range(limit)]
            elif series_id == "DGS10":
                values = [4.5 + (i % 15) * 0.1 for i in range(limit)]
            elif series_id == "DGS2":
                values = [4.8 + (i % 12) * 0.1 for i in range(limit)]
            else:
                values = [100 + i * 0.5 for i in range(limit)]
            
            return pd.DataFrame({
                'date': dates,
                'value': values
            })
        
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "limit": limit
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(self.base_url, params=params)
            r.raise_for_status()
            data = r.json()
        
        observations = data.get("observations", [])
        df = pd.DataFrame(observations)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df = df.dropna()
        
        return df

class MacroAnalyzer:
    def __init__(self):
        self.fred = FREDClient(FRED_API_KEY)
    
    async def get_latest_snapshot(self) -> MacroSnapshot:
        """Get latest macro economic snapshot"""
        try:
            # Fetch key series
            cpi_df = await self.fred.fetch_series("CPIAUCSL", 24)  # Monthly CPI
            unrate_df = await self.fred.fetch_series("UNRATE", 12)  # Unemployment
            ffr_df = await self.fred.fetch_series("FEDFUNDS", 12)  # Fed Funds Rate
            dgs10_df = await self.fred.fetch_series("DGS10", 30)  # 10Y Treasury
            dgs2_df = await self.fred.fetch_series("DGS2", 30)   # 2Y Treasury
            
            snapshot = MacroSnapshot(as_of_date=date.today())
            
            # Calculate inflation YoY
            if len(cpi_df) >= 12:
                latest_cpi = cpi_df.iloc[-1]["value"]
                year_ago_cpi = cpi_df.iloc[-12]["value"]
                snapshot.inflation_yoy = (latest_cpi / year_ago_cpi - 1) if year_ago_cpi > 0 else None
            
            # Latest unemployment rate
            if not unrate_df.empty:
                snapshot.unemployment_rate = unrate_df.iloc[-1]["value"] / 100  # Convert to decimal
            
            # Latest policy rate
            if not ffr_df.empty:
                snapshot.policy_rate = ffr_df.iloc[-1]["value"] / 100  # Convert to decimal
            
            # Yield curve spread
            if not dgs10_df.empty and not dgs2_df.empty:
                latest_10y = dgs10_df.iloc[-1]["value"]
                latest_2y = dgs2_df.iloc[-1]["value"]
                if pd.notna(latest_10y) and pd.notna(latest_2y):
                    snapshot.yc_10y_2y = (latest_10y - latest_2y) / 100  # Convert to decimal
                    # Recession proxy: inverted yield curve
                    snapshot.recession_proxy = snapshot.yc_10y_2y < 0
            
            return snapshot
            
        except Exception as e:
            # Return default snapshot on error
            return MacroSnapshot(as_of_date=date.today())

class SentimentAnalyzer:
    def __init__(self):
        pass
    
    async def get_ticker_sentiment(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """Get sentiment analysis for a ticker"""
        # Dummy implementation - in real version would query news sources
        import random
        random.seed(hash(symbol) % 1000)
        
        avg_score = random.uniform(-0.3, 0.3)  # Slightly positive bias
        n_articles = random.randint(5, 50)
        geopolitics_flag = random.random() < 0.1  # 10% chance
        
        return {
            "symbol": symbol,
            "window_days": days,
            "avg_score": avg_score,
            "n_articles": n_articles,
            "geopolitics_flag": geopolitics_flag,
            "last_updated": datetime.now().isoformat()
        }

class RiskGauges:
    def __init__(self):
        pass
    
    async def get_market_risk(self) -> Dict[str, Any]:
        """Get market risk indicators"""
        # Dummy implementation - in real version would fetch VIX, put/call ratios
        import random
        
        vix = random.uniform(15, 35)
        vix_percentile = random.uniform(0.2, 0.8)
        put_call_ratio = random.uniform(0.8, 1.2)
        breadth_pct = random.uniform(0.3, 0.8)
        
        return {
            "vix": vix,
            "vix_percentile_3y": vix_percentile,
            "put_call_ratio": put_call_ratio,
            "pct_spx_above_ma200": breadth_pct,
            "last_updated": datetime.now().isoformat()
        }

# Initialize analyzers
macro_analyzer = MacroAnalyzer()
sentiment_analyzer = SentimentAnalyzer()
risk_gauges = RiskGauges()

@app.get("/macro/snapshot")
async def macro_snapshot():
    """Get latest macroeconomic snapshot"""
    snapshot = await macro_analyzer.get_latest_snapshot()
    return {
        "as_of_date": snapshot.as_of_date.isoformat(),
        "inflation_yoy": float(snapshot.inflation_yoy) if snapshot.inflation_yoy is not None else None,
        "core_inflation_yoy": float(snapshot.core_inflation_yoy) if snapshot.core_inflation_yoy is not None else None,
        "unemployment_rate": float(snapshot.unemployment_rate) if snapshot.unemployment_rate is not None else None,
        "policy_rate": float(snapshot.policy_rate) if snapshot.policy_rate is not None else None,
        "yc_10y_2y": float(snapshot.yc_10y_2y) if snapshot.yc_10y_2y is not None else None,
        "recession_proxy": bool(snapshot.recession_proxy)
    }

@app.get("/macro/series")
async def macro_series(code: str):
    """Get time series data for a macro indicator"""
    try:
        df = await macro_analyzer.fred.fetch_series(code, 100)
        if df.empty:
            raise HTTPException(404, f"No data found for series {code}")
        
        return {
            "series_id": code,
            "data": [
                {"date": row["date"].isoformat(), "value": row["value"]}
                for _, row in df.iterrows()
            ]
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch series {code}: {str(e)}")

@app.get("/sentiment/ticker/{symbol}")
async def ticker_sentiment(symbol: str):
    """Get sentiment analysis for a specific ticker"""
    try:
        sentiment = await sentiment_analyzer.get_ticker_sentiment(symbol.upper())
        return sentiment
    except Exception as e:
        raise HTTPException(500, f"Failed to get sentiment for {symbol}: {str(e)}")

@app.get("/risk/market")
async def market_risk():
    """Get market risk indicators"""
    try:
        risk_data = await risk_gauges.get_market_risk()
        return risk_data
    except Exception as e:
        raise HTTPException(500, f"Failed to get market risk: {str(e)}")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "macro_sentiment_api",
        "fred_key_configured": bool(FRED_API_KEY)
    }

# Scoring functions for integration with stock analyzer
def score_macro_regime(snapshot: MacroSnapshot) -> int:
    """Score macro regime (0-10 points)"""
    points = 0
    
    if snapshot.inflation_yoy is not None:
        if snapshot.inflation_yoy < 0.03:  # Below 3%
            points += 3
        elif snapshot.inflation_yoy < 0.05:  # Below 5%
            points += 1
    
    if snapshot.yc_10y_2y is not None:
        if snapshot.yc_10y_2y > 0:  # Normal yield curve
            points += 3
        elif snapshot.yc_10y_2y > -0.005:  # Slightly inverted
            points += 1
    
    if snapshot.unemployment_rate is not None:
        if snapshot.unemployment_rate < 0.05:  # Below 5%
            points += 2
        elif snapshot.unemployment_rate < 0.07:  # Below 7%
            points += 1
    
    if snapshot.recession_proxy:
        points -= 4
    
    return max(0, min(10, points))

def score_market_risk(vix_percentile: float, put_call_ratio: float, breadth_pct: float) -> int:
    """Score market risk (0-10 points)"""
    points = 0
    
    if vix_percentile < 0.3:
        points += 4
    elif vix_percentile < 0.6:
        points += 2
    
    if put_call_ratio < 1.0:  # More calls than puts
        points += 2
    
    if breadth_pct > 0.6:  # Good breadth
        points += 2
    elif breadth_pct < 0.3:  # Poor breadth
        points -= 2
    
    return max(0, min(10, points))

def score_sentiment(avg_score: float, geopolitics_flag: bool) -> int:
    """Score news sentiment (0-10 points)"""
    # Map -1..1 to 0..10
    points = int(round((avg_score + 1) * 5))
    
    if geopolitics_flag:
        points -= 3
    
    return max(0, min(10, points))

@app.get("/scoring/macro")
async def get_macro_score():
    """Get macro regime score for stock analysis"""
    snapshot = await macro_analyzer.get_latest_snapshot()
    score = score_macro_regime(snapshot)
    return {
        "score": int(score),
        "max_score": 10,
        "snapshot": {
            "as_of_date": snapshot.as_of_date.isoformat(),
            "inflation_yoy": float(snapshot.inflation_yoy) if snapshot.inflation_yoy is not None else None,
            "unemployment_rate": float(snapshot.unemployment_rate) if snapshot.unemployment_rate is not None else None,
            "policy_rate": float(snapshot.policy_rate) if snapshot.policy_rate is not None else None,
            "yc_10y_2y": float(snapshot.yc_10y_2y) if snapshot.yc_10y_2y is not None else None,
            "recession_proxy": bool(snapshot.recession_proxy)
        }
    }

@app.get("/scoring/market_risk")
async def get_market_risk_score():
    """Get market risk score for stock analysis"""
    risk_data = await risk_gauges.get_market_risk()
    score = score_market_risk(
        risk_data["vix_percentile_3y"],
        risk_data["put_call_ratio"],
        risk_data["pct_spx_above_ma200"]
    )
    return {"score": score, "max_score": 10, "risk_data": risk_data}

@app.get("/scoring/sentiment/{symbol}")
async def get_sentiment_score(symbol: str):
    """Get sentiment score for a specific ticker"""
    sentiment = await sentiment_analyzer.get_ticker_sentiment(symbol.upper())
    score = score_sentiment(sentiment["avg_score"], sentiment["geopolitics_flag"])
    return {"score": score, "max_score": 10, "sentiment": sentiment}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
