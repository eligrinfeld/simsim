from __future__ import annotations
import os
from dotenv import load_dotenv

# Load environment variables FIRST before any other imports
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

import asyncio, random, time, uuid, json, math, traceback
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
import re
from textblob import TextBlob
import feedparser
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Deque, Dict, List, Optional
from collections import defaultdict, deque
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import strategies as st
try:
    from supabase_client import supabase_client, SUPABASE_URL, SUPABASE_KEY
except ImportError:
    # Fallback if supabase module not available
    class MockSupabaseClient:
        enabled = False
        async def get_events(self, **kwargs): return []
        async def save_event(self, **kwargs): pass
    supabase_client = MockSupabaseClient()
    SUPABASE_URL = ""
    SUPABASE_KEY = ""

# Strategy orchestrator (grid search and ranking)
try:
    from strategy_orchestrator import evaluate_grid
except Exception:
    evaluate_grid = None  # safe fallback


# ---------- Event model ----------
@dataclass
class Event:
    type: str
    ts: float = field(default_factory=lambda: time.time())
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

# Convenience events
def Bar(symbol: str, o: float, h: float, l: float, c: float, v: float) -> Event:
    return Event("Bar", key=symbol, data={"open": o, "high": h, "low": l, "close": c, "volume": v})

def NewsItem(symbol: str, sentiment: float, headline: str) -> Event:
    return Event("NewsItem", key=symbol, data={"sentiment": sentiment, "headline": headline})

def MacroRelease(series: str, actual: float = 0, estimate: float = 0, surprise: float = 0) -> Event:
    return Event("MacroRelease", key=series, data={"series": series, "actual": actual, "estimate": estimate, "surprise": surprise or (actual - estimate)})

def MacroShock(series: str, magnitude: float) -> Event:
    return Event("MacroShock", key=series, data={"series": series, "magnitude": magnitude})

# ---------- Simple CEP core ----------
class EventSink:
    def __init__(self):
        self._subs: List[Callable[[Event], Any]] = []
    def subscribe(self, fn: Callable[[Event], Any]):
        self._subs.append(fn)
    def emit(self, evt: Event):
        for fn in list(self._subs):
            fn(evt)

class CEP:
    def __init__(self):
        self.sink = EventSink()
        self._rules: List[Callable[[Event], None]] = []

    def ingest(self, evt: Event):
        for r in self._rules:
            r(evt)

    # A then B within T (per key)
    def on_sequence(self, *, name: str, first_type: str, then_type: str, within_sec: float,
                    where_first=None, where_then=None, emit_type="SequenceMatched"):
        states: Dict[str, Deque[Event]] = defaultdict(deque)
        def rule(evt: Event):
            k, now = evt.key or "", evt.ts
            q = states[k]
            while q and (now - q[0].ts) > within_sec:
                q.popleft()
            if evt.type == first_type:
                if not where_first or where_first(evt):
                    q.append(evt)
            elif evt.type == then_type:
                for a in reversed(q):
                    if (not where_first or where_first(a)) and (not where_then or where_then(a, evt)):
                        self.sink.emit(Event(emit_type, key=k, ts=evt.ts, data={"rule": name, "first": a.to_dict(), "then": evt.to_dict()}))
                        try:
                            q.remove(a)
                        except ValueError:
                            pass
                        break
        self._rules.append(rule)

    # Sliding count >= threshold (per key)
    def on_sliding_count(self, *, name: str, event_type: str, within_sec: float, threshold: int,
                         where=None, emit_type="ThresholdHit"):
        buckets: Dict[str, Deque[Event]] = defaultdict(deque)
        def rule(evt: Event):
            if evt.type != event_type:
                return
            if where and not where(evt):
                return
            k, now = evt.key or "", evt.ts
            q = buckets[k]; q.append(evt)
            while q and (now - q[0].ts) > within_sec:
                q.popleft()
            if len(q) >= threshold:
                self.sink.emit(Event(emit_type, key=k, ts=evt.ts, data={"rule": name, "count": len(q), "last": evt.to_dict()}))
        self._rules.append(rule)

    # Macro shock detector (simple example)
    def on_macro_shock(self, *, series: str, surprise_abs_ge: float, emit_type="MacroShock"):
        def rule(evt: Event):
            if evt.type == "MacroRelease" and evt.data.get("series") == series:
                surprise = abs(evt.data.get("surprise", 0.0))
                if surprise >= surprise_abs_ge:
                    self.sink.emit(Event(emit_type, key=series, ts=evt.ts, data={"series": series, "surprise": evt.data["surprise"]}))
        self._rules.append(rule)

# ---------- FastAPI app & live push ----------
app = FastAPI(title="Event Dashboard")
# Serve static assets under /static and index at /
app.mount("/static", StaticFiles(directory="public"), name="static")

@app.get("/")
async def index():
    # Serve the SPA index
    return FileResponse("public/index.html")


DEFAULT_SYMBOL = "SPY"
SUPPORTED_SYMBOLS = ["SPY", "QQQ", "AAPL", "MSFT", "TSLA", "NVDA"]
candles: Dict[str, List[Dict[str, Any]]] = {symbol: [] for symbol in SUPPORTED_SYMBOLS}
clients: List[WebSocket] = []
clients_lock = asyncio.Lock()

# Keep a small backfill buffer of recent non-Bar events
RECENT_MAX = 500
recent_events: Deque[Dict[str, Any]] = deque(maxlen=RECENT_MAX)

# Latest quote snapshot per symbol (from Yahoo Finance info)
latest_quotes: Dict[str, Dict[str, Any]] = {}

cep = CEP()

async def broadcast(evt: Event):
    msg = {"type": evt.type, "key": evt.key, "ts": int(evt.ts), "data": evt.data}
    # Save all events to Supabase (raw + derived)
    asyncio.create_task(supabase_client.save_event(msg))
    # Store non-Bar events for backfill
    if evt.type != "Bar":
        recent_events.append(msg)
    async with clients_lock:
        dead: List[WebSocket] = []
        for ws in clients:
            try:
                await ws.send_json(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            try:
                clients.remove(ws)
            except ValueError:
                pass

# Connect CEP → frontend
# Forward CEP events to frontend; persistence handled in broadcast
cep.sink.subscribe(lambda e: asyncio.create_task(broadcast(e)))

@app.get("/candles")
async def get_candles(symbol: str = DEFAULT_SYMBOL, interval: str | None = None, period: str | None = None):
    """Return candles.
    - If no interval provided: return recent in-memory candles (1m)
    - If interval provided: fetch from Yahoo Finance on demand using sensible defaults
    """
    try:
        if not interval:
            if symbol not in candles:
                return JSONResponse([])
            return JSONResponse(candles[symbol][-2000:])

        # Map common intervals to default periods
        tf_defaults = {
            "1m": ("1d", "1m"),
            "5m": ("5d", "5m"),
            "15m": ("1mo", "15m"),
            "30m": ("1mo", "30m"),
            "1h": ("1mo", "1h"),
            "1d": ("6mo", "1d"),
            "1wk": ("2y", "1wk"),
            "1mo": ("5y", "1mo"),
        }
        p, itv = tf_defaults.get(interval, (period or "1mo", interval))
        if period:
            p = period
        data = await fetch_live_price_data(symbol, period=p, interval=itv)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/symbols")
async def get_symbols():
    """Get list of supported symbols with current prices and percent change.
    Prefers latest_quotes (from Yahoo) for accurate day change and volume; falls back to last candle.
    """
    symbols_info = []
    for symbol in SUPPORTED_SYMBOLS:
        q = latest_quotes.get(symbol)
        if q:
            symbols_info.append({
                "symbol": symbol,
                "price": q.get("price", 0),
                "change": q.get("change", 0),
                # Normalize to fraction (e.g., 0.0007 = 0.07%) so clients can *100
                "changePercent": (q.get("changePercent", 0) or 0) / 100.0,
                "volume": q.get("volume", 0),
            })
            continue
        if symbol in candles and len(candles[symbol]) > 0:
            latest = candles[symbol][-1]
            prev_open = latest.get("open", 0)
            close = latest.get("close", 0)
            ch = close - prev_open
            pct = (ch / prev_open) if prev_open else 0
            symbols_info.append({
                "symbol": symbol,
                "price": close,
                "change": ch,
                "changePercent": pct,
                "volume": latest.get("volume", 0)
            })
        else:
            symbols_info.append({"symbol": symbol, "price": 0, "change": 0, "changePercent": 0, "volume": 0})
    return JSONResponse(symbols_info)


@app.get("/sentiment/{symbol}")
async def get_sentiment_scores(symbol: str):
    """Get X sentiment scores for a symbol."""
    if symbol not in symbol_sentiment_scores:
        return JSONResponse({"error": f"Symbol {symbol} not supported"})

    scores = symbol_sentiment_scores[symbol]
    return JSONResponse({
        "symbol": symbol,
        "sentiment_scores": scores[-50:],  # Last 50 scores
        "current_score": scores[-1]["score"] if scores else 0.0,
        "count": len(scores)
    })


@app.get("/sentiment")
async def get_all_sentiment_scores():
    """Get current X sentiment scores for all symbols."""
    sentiment_summary = {}

    for symbol in SUPPORTED_SYMBOLS:
        scores = symbol_sentiment_scores[symbol]
        if scores:
            latest = scores[-1]
            sentiment_summary[symbol] = {
                "current_score": latest["score"],
                "timestamp": latest["timestamp"],
                "total_analyses": len(scores)
            }
        else:
            sentiment_summary[symbol] = {
                "current_score": 0.0,
                "timestamp": 0,
                "total_analyses": 0
            }

    return JSONResponse(sentiment_summary)


@app.get("/data/status")
async def get_data_persistence_status():
    """Get comprehensive data persistence status."""
    # Ensure 'enabled' is a boolean for JSON output
    supa_enabled = bool(getattr(supabase_client, 'enabled', False))
    return JSONResponse({
        "supabase": {
            "enabled": supa_enabled,
            "url": SUPABASE_URL[:30] + "..." if SUPABASE_URL else "Not set",
            "key_configured": bool(SUPABASE_KEY),
            "tables": {
                "events": "All CEP events (NewsItem, Breakout, XSentiment, etc.)",
                "market_data": "Live OHLCV price data from Yahoo Finance",
                "news_articles": "RSS feed articles with sentiment analysis",
                "economic_data": "FRED/Alpha Vantage economic indicators",
                "sentiment_analysis": "Full Grok X sentiment analysis",
                "pine_strategies": "User-created trading strategies",
                "pine_results": "Strategy backtest results",
                "user_sessions": "Analysis sessions and metadata"
            }
        },
        "local_storage": {
            "candles": {symbol: len(candles[symbol]) for symbol in SUPPORTED_SYMBOLS},
            "sentiment_scores": {symbol: len(symbol_sentiment_scores[symbol]) for symbol in SUPPORTED_SYMBOLS},
            "recent_events": len(recent_events)
        },
        "data_sources": {
            "market_data": "Yahoo Finance API (live prices)",
            "news": "RSS feeds (Yahoo Finance, MarketWatch, Bloomberg, CNBC)",
            "economic": "FRED API, Alpha Vantage, Economic RSS feeds",
            "sentiment": "Grok API (X/Twitter analysis)",
            "api_keys": {
                "GROK_API_KEY": bool(GROK_API_KEY),
                "NEWS_API_KEY": bool(NEWS_API_KEY),
                "ALPHA_VANTAGE_KEY": bool(ALPHA_VANTAGE_KEY),
                "FRED_API_KEY": bool(FRED_API_KEY)
            }
        }
    })

@app.get("/events")
async def get_events(since: Optional[int] = None):
    if since is None:
        return JSONResponse(list(recent_events))
    try:
        s = int(since)
    except Exception:
        s = 0
    data = [e for e in list(recent_events) if int(e.get("ts", 0)) > s]
    return JSONResponse(data)

@app.get("/strategy/best")
async def best_strategy(symbol: str = DEFAULT_SYMBOL):
    # Use the last N candles to evaluate strategies
    if symbol not in candles or len(candles[symbol]) < 400:
        return JSONResponse({"error": f"Insufficient data for {symbol}"})
    window = candles[symbol][-400:]
    best = st.pick_best(window)
    expl = st.explain(best)
    return JSONResponse({

@app.get("/strategy/run")
async def strategy_run(symbol: str = DEFAULT_SYMBOL, timeframe: str = "1m"):
    """Run a quick grid search over built-in strategies (and any available Pine).
    For now, this is synchronous and returns top results. Later we can persist.
    """
    if evaluate_grid is None:
        return JSONResponse(status_code=503, content={"error": "orchestrator unavailable"})
    try:
        # Fetch candles matching timeframe: use /candles logic for simplicity
        if timeframe == "1m":
            if symbol not in candles or len(candles[symbol]) < 100:
                return JSONResponse({"error": f"Insufficient data for {symbol}"})
            window = candles[symbol][-600:]
        else:
            data = await fetch_live_price_data(symbol, period=("1mo" if timeframe in ("15m","30m","1h") else "6mo"), interval=timeframe)
            window = data[-600:]
        ranked = evaluate_grid(window)
        top = [
            {
                "name": r.name,
                "total_return": float(r.total_return or 0.0),
                "sharpe": float(r.sharpe or 0.0),
                "max_drawdown": float(r.max_drawdown or 0.0),
                "trades": r.trades,
            }
            for r in ranked[:5]
        ]
        return JSONResponse({"results": top})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/strategy/best2")
async def strategy_best2(symbol: str = DEFAULT_SYMBOL, timeframe: str = "1m"):
    if evaluate_grid is None:
        return JSONResponse(status_code=503, content={"error": "orchestrator unavailable"})
    try:
        # Reuse run logic but return only best
        if timeframe == "1m":
            if symbol not in candles or len(candles[symbol]) < 100:
                return JSONResponse({"error": f"Insufficient data for {symbol}"})
            window = candles[symbol][-600:]
        else:
            data = await fetch_live_price_data(symbol, period=("1mo" if timeframe in ("15m","30m","1h") else "6mo"), interval=timeframe)
            window = data[-600:]
        ranked = evaluate_grid(window)
        if not ranked:
            return JSONResponse({"error": "no results"})
        best = ranked[0]
        expl = st.explain(st.BacktestResult(best.name, best.total_return, best.sharpe, best.max_drawdown, best.trades, best.details))
        return JSONResponse({
            "name": best.name,
            "total_return": float(best.total_return or 0.0),
            "sharpe": float(best.sharpe or 0.0),
            "max_drawdown": float(best.max_drawdown or 0.0),
            "trades": best.trades,
            "explanation": expl,
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

        "name": best.name,
        "total_return": best.total_return,
        "sharpe": best.sharpe,
        "max_drawdown": best.max_drawdown,
        "trades": best.trades,
        "explanation": expl,
    })

from pine_adapter import compile_pine

@app.post("/strategy/pine/preview")
async def pine_preview(payload: Dict[str, Any]):
    try:
        code = payload.get("code", "") if isinstance(payload, dict) else ""
        if not code:
            return JSONResponse(status_code=400, content={"error": "missing code"})
        # Ensure we have some candles for evaluation; if the live loop hasn't produced any yet, seed a few
        if not candles:
            base = 450.0
            last = base
            for _ in range(50):
                k = next_candle(last); last = k["close"]; candles.append(k)
        comp = compile_pine(code)
        window = candles[-400:] if len(candles) >= 2 else candles
        res = comp.run(window)
        return JSONResponse({
            "compiled": {"name": comp.name, "params": comp.params, "series": comp.series, "rules": comp.rules},
            "result": {
                "name": res.name,
                "total_return": float(res.total_return or 0.0),
                "sharpe": float(res.sharpe or 0.0),
                "max_drawdown": float(res.max_drawdown or 0.0),
                "trades": res.trades,
            }
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/strategy/pine/save")
async def save_pine_strategy(payload: Dict[str, Any]):
    """Save a Pine strategy to Supabase."""
    try:
        name = payload.get("name", "")
        code = payload.get("code", "")
        description = payload.get("description", "")
        parameters = payload.get("parameters", {})
        user_id = payload.get("user_id", "anonymous")  # In real app, get from auth

        if not name or not code:
            return JSONResponse(status_code=400, content={"error": "name and code are required"})

        strategy_id = await supabase_client.save_pine_strategy(
            user_id=user_id,
            name=name,
            code=code,
            parameters=parameters,
            description=description
        )

        return JSONResponse({
            "success": True,
            "strategy_id": strategy_id,
            "message": f"Strategy '{name}' saved successfully"
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/strategy/pine/list")
async def list_pine_strategies(user_id: str = "anonymous"):
    """List all Pine strategies for a user."""
    try:
        strategies = await supabase_client.get_user_strategies(user_id)
        return JSONResponse({
            "strategies": strategies,
            "count": len(strategies)
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/strategy/pine/result/save")
async def save_pine_result(payload: Dict[str, Any]):
    """Save Pine backtest results to Supabase."""
    try:
        strategy_id = payload.get("strategy_id", "")
        symbol = payload.get("symbol", "SPY")
        timeframe = payload.get("timeframe", "1m")
        result = payload.get("result", {})

        if not strategy_id:
            return JSONResponse(status_code=400, content={"error": "strategy_id is required"})

        result_id = await supabase_client.save_pine_result(
            strategy_id=strategy_id,
            symbol=symbol,
            timeframe=timeframe,
            sharpe_ratio=float(result.get("sharpe", 0)),
            total_return=float(result.get("total_return", 0)),
            max_drawdown=float(result.get("max_drawdown", 0)),
            trade_count=len(result.get("trades", [])),
            trades=result.get("trades", [])
        )

        return JSONResponse({
            "success": True,
            "result_id": result_id,
            "message": "Results saved successfully"
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/events/replay")
async def get_events_for_replay(symbol: str = None, since: int = None, until: int = None, types: str = None):
    """Get events for replay functionality. Query Supabase or fallback to recent_events."""
    try:
        event_types = types.split(",") if types else None

        # Try Supabase first
        events = await supabase_client.get_events(
            symbol=symbol,
            since_ts=since,
            until_ts=until,
            event_types=event_types
        )

        # Fallback to in-memory recent_events if Supabase returns empty or unavailable
        if not events and recent_events:
            filtered_events = recent_events

            if symbol:
                filtered_events = [e for e in filtered_events if e.get("key") == symbol]
            if since:
                filtered_events = [e for e in filtered_events if e.get("ts", 0) >= since]
            if until:
                filtered_events = [e for e in filtered_events if e.get("ts", 0) <= until]
            if event_types:
                filtered_events = [e for e in filtered_events if e.get("type") in event_types]

            events = sorted(filtered_events, key=lambda x: x.get("ts", 0))

        return JSONResponse({
            "events": events,
            "count": len(events),
            "source": "supabase" if events and supabase_client.enabled else "memory"
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/events/explain")
async def explain_event(request: Request):
    """Generate AI explanation for why a CEP event fired."""
    try:
        data = await request.json()
        event_type = data.get("type")
        event_data = data.get("data", {})
        event_key = data.get("key")
        event_ts = data.get("ts")

        # Generate explanation based on event type
        explanation = generate_event_explanation(event_type, event_data, event_key, event_ts)

        return JSONResponse({
            "explanation": explanation,
            "event_type": event_type,
            "timestamp": event_ts
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


def generate_event_explanation(event_type: str, event_data: dict, key: str, ts: int) -> dict:
    """Generate detailed explanation for CEP events."""

    if event_type == "NewsBurst":
        return {
            "title": "News Burst Detected",
            "summary": f"Multiple positive news items for {key} triggered a news burst signal.",
            "details": [
                f"**Trigger Condition**: 3+ positive news items within 120 seconds",
                f"**Sentiment Threshold**: Articles with sentiment ≥ 0.6",
                f"**Symbol**: {key}",
                f"**Time Window**: 2-minute sliding window"
            ],
            "reasoning": "News bursts often precede significant price movements as market sentiment shifts rapidly. This pattern suggests increased attention and potential volatility.",
            "confidence": "High",
            "action_suggestion": "Monitor for price breakouts or increased volume in the next 5-10 minutes."
        }

    elif event_type == "MacroShock":
        return {
            "title": "Macro Economic Shock",
            "summary": f"Significant macro event detected with potential market-wide impact.",
            "details": [
                f"**Event Type**: {event_data.get('type', 'Economic Release')}",
                f"**Magnitude**: {event_data.get('magnitude', 'High')}",
                f"**Affected Sectors**: Broad market impact expected",
                f"**Time Sensitivity**: Immediate to 1-hour impact window"
            ],
            "reasoning": "Macro shocks can cause correlated moves across asset classes. This event suggests reviewing portfolio risk exposure and potential hedging needs.",
            "confidence": "High",
            "action_suggestion": "Consider reducing position sizes or adding hedges until market digests the news."
        }

    elif event_type == "Breakout":
        price = event_data.get("price", 0)
        lookback = event_data.get("lookback", 20)
        return {
            "title": "Price Breakout Signal",
            "summary": f"{key} broke above its {lookback}-period high at ${price:.2f}.",
            "details": [
                f"**Breakout Price**: ${price:.2f}",
                f"**Lookback Period**: {lookback} periods",
                f"**Pattern**: Higher high formation",
                f"**Volume**: Monitor for confirmation"
            ],
            "reasoning": f"Breakouts above {lookback}-period highs often signal continuation of upward momentum. This suggests buyers are willing to pay higher prices.",
            "confidence": "Medium",
            "action_suggestion": f"Consider entry on pullback to ${price:.2f} support level with stop below recent low."
        }

    elif event_type == "TradeEntryIntent":
        return {
            "title": "Trade Entry Signal",
            "summary": f"Algorithm identified potential trade opportunity in {key}.",
            "details": [
                f"**Signal Strength**: {event_data.get('confidence', 'Medium')}",
                f"**Entry Reason**: {event_data.get('reason', 'Technical pattern')}",
                f"**Risk Level**: {event_data.get('risk', 'Standard')}",
                f"**Time Horizon**: {event_data.get('horizon', 'Short-term')}"
            ],
            "reasoning": "Multiple factors aligned to suggest favorable risk/reward setup. This represents a systematic opportunity based on historical patterns.",
            "confidence": event_data.get('confidence', 'Medium'),
            "action_suggestion": "Review position sizing and risk management before entry."
        }

    elif event_type == "XSentiment":
        score = event_data.get("sentiment_score", 0)
        direction = "bullish" if score > 0 else "bearish" if score < 0 else "neutral"
        return {
            "title": "X (Twitter) Sentiment Analysis",
            "summary": f"Social media sentiment for {key} is {direction} with score {score:.2f}.",
            "details": [
                f"**Sentiment Score**: {score:.2f} (-1 to +1 scale)",
                f"**Direction**: {direction.title()}",
                f"**Source**: X (Twitter) via Grok AI",
                f"**Analysis**: Real-time social media sentiment"
            ],
            "reasoning": "Social media sentiment often precedes or confirms price movements. Strong sentiment can indicate retail investor interest and potential momentum.",
            "confidence": "Medium",
            "action_suggestion": f"Monitor for price correlation with {direction} sentiment. Consider position sizing based on sentiment strength."
        }

    elif event_type == "StrongXSentiment":
        score = event_data.get("sentiment_score", 0)
        direction = event_data.get("direction", "neutral")
        magnitude = event_data.get("magnitude", 0)
        return {
            "title": "Strong X Sentiment Signal",
            "summary": f"Very strong {direction} sentiment detected for {key} (score: {score:.2f}).",
            "details": [
                f"**Sentiment Score**: {score:.2f}",
                f"**Direction**: {direction.title()}",
                f"**Magnitude**: {magnitude:.2f}",
                f"**Threshold**: ≥0.7 for strong sentiment"
            ],
            "reasoning": "Extreme social media sentiment often correlates with significant price movements. This level of sentiment suggests strong retail interest.",
            "confidence": "High",
            "action_suggestion": f"Strong {direction} sentiment may drive price action. Consider {'long' if direction == 'bullish' else 'short'} positions with tight risk management."
        }

    elif event_type == "SentimentConfirmedBreakout":
        return {
            "title": "Sentiment-Confirmed Breakout",
            "summary": f"Price breakout for {key} confirmed by strong social media sentiment.",
            "details": [
                f"**Pattern**: Breakout + Strong Sentiment",
                f"**Timeframe**: Sentiment preceded breakout within 30 minutes",
                f"**Confirmation**: Social media aligns with price action",
                f"**Signal Strength**: High (dual confirmation)"
            ],
            "reasoning": "When strong social sentiment precedes a price breakout, it suggests the move has both technical and fundamental backing from retail sentiment.",
            "confidence": "High",
            "action_suggestion": "High-confidence signal for trend continuation. Consider increasing position size with appropriate risk management."
        }

    elif event_type == "SentimentDivergence":
        return {
            "title": "Sentiment-Price Divergence",
            "summary": f"Social media sentiment diverging from price action for {key}.",
            "details": [
                f"**Pattern**: Sentiment vs Price Divergence",
                f"**Window**: Multiple sentiment readings in 1 hour",
                f"**Signal**: Potential reversal or continuation",
                f"**Analysis**: Social sentiment not matching price"
            ],
            "reasoning": "Divergence between social sentiment and price can signal either a pending reversal or a false sentiment reading. Requires additional confirmation.",
            "confidence": "Medium",
            "action_suggestion": "Monitor for resolution of divergence. Wait for price or sentiment to align before taking positions."
        }

    else:
        return {
            "title": f"{event_type} Event",
            "summary": f"CEP detected a {event_type} event for {key}.",
            "details": [
                f"**Event Type**: {event_type}",
                f"**Symbol**: {key}",
                f"**Data**: {str(event_data)[:100]}..."
            ],
            "reasoning": "This event was triggered by the Complex Event Processing engine based on predefined rules and thresholds.",
            "confidence": "Medium",
            "action_suggestion": "Review event details and consider impact on trading strategy."
        }


# Live data fetching functions
async def fetch_live_price_data(symbol: str, period: str = "1d", interval: str = "1m") -> List[Dict[str, Any]]:
    """Fetch live price data from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)

        if hist.empty:
            print(f"⚠️ No data received for {symbol}")
            return []

        candles = []
        for timestamp, row in hist.iterrows():
            candles.append({
                "time": int(timestamp.timestamp()),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume'])
            })

        print(f"✅ Fetched {len(candles)} candles for {symbol}")
        return candles

    except Exception as e:
        print(f"❌ Failed to fetch data for {symbol}: {e}")
        return []


async def get_latest_price(symbol: str) -> Dict[str, Any]:
    """Get the latest price for a symbol."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Pull both live/regular fields and normalize
        price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        ch_abs = info.get('regularMarketChange', 0)
        ch_pct_raw = info.get('regularMarketChangePercent', 0)
        # If Yahoo returned percent as e.g., 0.73 (meaning 0.73%), convert to fraction
        ch_pct = (ch_pct_raw or 0) / 100.0
        # If unavailable, derive from absolute change
        if not ch_pct and price:
            prev = price - ch_abs
            ch_pct = (ch_abs / prev) if prev else 0
        q = {
            "symbol": symbol,
            "price": price,
            "change": ch_abs,
            "changePercent": ch_pct,
            "volume": info.get('regularMarketVolume', 0),
            "timestamp": int(time.time())
        }
        latest_quotes[symbol] = q
        return q
    except Exception as e:
        print(f"❌ Failed to get latest price for {symbol}: {e}")
        return {"symbol": symbol, "price": 0, "change": 0, "changePercent": 0, "volume": 0, "timestamp": int(time.time())}


async def initialize_live_data():
    """Initialize live data for all supported symbols."""
    print("🔄 Initializing live market data...")

    for symbol in SUPPORTED_SYMBOLS:
        print(f"Fetching data for {symbol}...")
        live_candles = await fetch_live_price_data(symbol, period="5d", interval="1m")

        if live_candles:
            candles[symbol] = live_candles[-2000:]  # Keep last 2000 candles
            print(f"✅ Loaded {len(candles[symbol])} candles for {symbol}")

            # Save market data to Supabase
            await supabase_client.save_market_data(symbol, live_candles)
        else:
            # Fallback to simulated data if live data fails
            print(f"⚠️ Using simulated data for {symbol}")
            base_prices = {"SPY": 450.0, "QQQ": 380.0, "AAPL": 180.0, "MSFT": 420.0, "TSLA": 250.0, "NVDA": 900.0}
            base = base_prices.get(symbol, 100.0)
            last = base
            sim_candles = []
            for i in range(200):
                k = next_candle(last)
                last = k["close"]
                sim_candles.append(k)
            candles[symbol] = sim_candles

    print("✅ Live data initialization complete")


# Live news and macro data fetching functions
NEWS_API_KEY = os.getenv("NEWS_API_KEY")  # Get from newsapi.org
ALPHA_VANTAGE_KEY = os.getenv("ALPHAVANTAGE_API_KEY")  # Get from alphavantage.co
FRED_API_KEY = os.getenv("FRED_API_KEY")  # Get from fred.stlouisfed.org
GROK_API_KEY = os.getenv("GROK_API_KEY")  # Get from x.ai

def analyze_sentiment(text: str) -> float:
    """Analyze sentiment of text using TextBlob. Returns score between -1 and 1."""
    try:
        blob = TextBlob(text)
        return blob.sentiment.polarity
    except:
        return 0.0

def extract_symbols_from_text(text: str) -> List[str]:
    """Extract stock symbols mentioned in news text."""
    text_upper = text.upper()
    mentioned_symbols = []

    # Check for direct symbol mentions
    for symbol in SUPPORTED_SYMBOLS:
        if symbol in text_upper:
            mentioned_symbols.append(symbol)

    # Check for company name mentions
    company_names = {
        "SPY": ["S&P 500", "SPY", "SPDR"],
        "QQQ": ["NASDAQ", "QQQ", "INVESCO"],
        "AAPL": ["APPLE", "IPHONE", "MAC", "IPAD"],
        "MSFT": ["MICROSOFT", "WINDOWS", "AZURE", "OFFICE"],
        "TSLA": ["TESLA", "ELON MUSK", "ELECTRIC VEHICLE", "EV"],
        "NVDA": ["NVIDIA", "GPU", "AI CHIP", "GRAPHICS"]
    }

    for symbol, names in company_names.items():
        for name in names:
            if name in text_upper and symbol not in mentioned_symbols:
                mentioned_symbols.append(symbol)
                break

    return mentioned_symbols if mentioned_symbols else ["SPY"]  # Default to SPY for market-wide news

async def fetch_newsapi_articles(symbol: str = None) -> List[Dict[str, Any]]:
    """Fetch news from NewsAPI."""
    if not NEWS_API_KEY:
        return []

    try:
        # Build query based on symbol
        if symbol and symbol != "SPY":
            company_queries = {
                "QQQ": "NASDAQ OR technology stocks",
                "AAPL": "Apple OR iPhone OR Tim Cook",
                "MSFT": "Microsoft OR Azure OR Satya Nadella",
                "TSLA": "Tesla OR Elon Musk OR electric vehicle",
                "NVDA": "Nvidia OR GPU OR AI chips"
            }
            query = company_queries.get(symbol, f"{symbol} stock")
        else:
            query = "stock market OR S&P 500 OR Wall Street"

        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 20,
            "apiKey": NEWS_API_KEY,
            "from": (datetime.now() - timedelta(hours=6)).isoformat()
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = []

            for article in data.get("articles", []):
                if article.get("title") and article.get("description"):
                    text = f"{article['title']} {article['description']}"
                    sentiment = analyze_sentiment(text)
                    symbols = extract_symbols_from_text(text)

                    articles.append({
                        "title": article["title"],
                        "description": article["description"],
                        "url": article.get("url", ""),
                        "publishedAt": article.get("publishedAt", ""),
                        "source": article.get("source", {}).get("name", "NewsAPI"),
                        "sentiment": sentiment,
                        "symbols": symbols
                    })

            return articles

    except Exception as e:
        print(f"❌ NewsAPI error: {e}")

    return []

async def fetch_alpha_vantage_news(symbol: str = None) -> List[Dict[str, Any]]:
    """Fetch news from Alpha Vantage."""
    if not ALPHA_VANTAGE_KEY:
        return []

    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": symbol if symbol else "SPY,QQQ,AAPL,MSFT,TSLA,NVDA",
            "limit": 50,
            "apikey": ALPHA_VANTAGE_KEY
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = []

            for item in data.get("feed", []):
                if item.get("title") and item.get("summary"):
                    # Alpha Vantage provides sentiment scores
                    sentiment_score = float(item.get("overall_sentiment_score", 0))

                    # Extract relevant tickers
                    ticker_sentiment = item.get("ticker_sentiment", [])
                    symbols = [t.get("ticker") for t in ticker_sentiment if t.get("ticker") in SUPPORTED_SYMBOLS]
                    if not symbols:
                        symbols = ["SPY"]

                    articles.append({
                        "title": item["title"],
                        "description": item["summary"][:200] + "..." if len(item["summary"]) > 200 else item["summary"],
                        "url": item.get("url", ""),
                        "publishedAt": item.get("time_published", ""),
                        "source": item.get("source", "Alpha Vantage"),
                        "sentiment": sentiment_score,
                        "symbols": symbols
                    })

            return articles

    except Exception as e:
        print(f"❌ Alpha Vantage News error: {e}")

    return []

async def fetch_rss_news() -> List[Dict[str, Any]]:
    """Fetch news from RSS feeds as fallback (no API key required)."""
    rss_feeds = [
        "https://feeds.finance.yahoo.com/rss/2.0/headline",
        "https://www.marketwatch.com/rss/topstories",
        "https://feeds.bloomberg.com/markets/news.rss",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html"
    ]

    articles = []

    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:5]:  # Limit to 5 articles per feed
                if hasattr(entry, 'title') and hasattr(entry, 'summary'):
                    text = f"{entry.title} {entry.summary}"
                    sentiment = analyze_sentiment(text)
                    symbols = extract_symbols_from_text(text)

                    # Only include if sentiment is strong enough
                    if abs(sentiment) >= 0.2:
                        articles.append({
                            "title": entry.title,
                            "description": entry.summary[:200] + "..." if len(entry.summary) > 200 else entry.summary,
                            "url": getattr(entry, 'link', ''),
                            "publishedAt": getattr(entry, 'published', ''),
                            "source": feed.feed.get('title', 'RSS Feed'),
                            "sentiment": sentiment,
                            "symbols": symbols
                        })

        except Exception as e:
            print(f"❌ RSS feed error for {feed_url}: {e}")
            continue

    return articles


# Live economic data fetching functions
async def fetch_fred_data(series_id: str, limit: int = 1) -> Dict[str, Any]:
    """Fetch economic data from FRED API."""
    if not FRED_API_KEY:
        return {}

    try:
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "limit": limit,
            "sort_order": "desc"
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            observations = data.get("observations", [])

            if observations:
                latest = observations[0]
                return {
                    "series_id": series_id,
                    "date": latest.get("date"),
                    "value": float(latest.get("value", 0)) if latest.get("value") != "." else None,
                    "source": "FRED"
                }

    except Exception as e:
        print(f"❌ FRED API error for {series_id}: {e}")

    return {}

async def fetch_alpha_vantage_economic_data() -> List[Dict[str, Any]]:
    """Fetch economic indicators from Alpha Vantage."""
    if not ALPHA_VANTAGE_KEY:
        return []

    indicators = [
        ("REAL_GDP", "Real GDP"),
        ("CPI", "Consumer Price Index"),
        ("INFLATION", "Inflation Rate"),
        ("UNEMPLOYMENT", "Unemployment Rate"),
        ("FEDERAL_FUNDS_RATE", "Federal Funds Rate")
    ]

    economic_data = []

    for indicator_code, indicator_name in indicators:
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": indicator_code,
                "apikey": ALPHA_VANTAGE_KEY,
                "datatype": "json"
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()

                # Different indicators have different data structures
                data_key = "data" if "data" in data else list(data.keys())[1] if len(data.keys()) > 1 else None

                if data_key and data_key in data:
                    indicator_data = data[data_key]
                    if isinstance(indicator_data, list) and len(indicator_data) > 0:
                        latest = indicator_data[0]
                        economic_data.append({
                            "indicator": indicator_name,
                            "code": indicator_code,
                            "date": latest.get("date"),
                            "value": float(latest.get("value", 0)) if latest.get("value") else None,
                            "source": "Alpha Vantage"
                        })

            # Rate limit - Alpha Vantage allows 5 calls per minute for free tier
            await asyncio.sleep(12)  # Wait 12 seconds between calls

        except Exception as e:
            print(f"❌ Alpha Vantage economic data error for {indicator_code}: {e}")
            continue

    return economic_data

async def fetch_economic_calendar() -> List[Dict[str, Any]]:
    """Fetch economic calendar events from various sources."""
    events = []

    # Try to get key economic indicators from FRED
    fred_indicators = [
        ("CPIAUCSL", "Consumer Price Index", "inflation"),
        ("UNRATE", "Unemployment Rate", "employment"),
        ("GDPC1", "Real GDP", "growth"),
        ("FEDFUNDS", "Federal Funds Rate", "monetary_policy"),
        ("PAYEMS", "Nonfarm Payrolls", "employment")
    ]

    for series_id, name, category in fred_indicators:
        try:
            data = await fetch_fred_data(series_id)
            if data and data.get("value") is not None:
                events.append({
                    "name": name,
                    "category": category,
                    "value": data["value"],
                    "date": data["date"],
                    "series_id": series_id,
                    "source": "FRED"
                })
        except Exception as e:
            print(f"❌ Error fetching {name}: {e}")
            continue

    return events

def calculate_economic_surprise(current_value: float, historical_values: List[float]) -> float:
    """Calculate economic surprise based on deviation from historical average."""
    if not historical_values or len(historical_values) < 2:
        return 0.0

    historical_avg = sum(historical_values) / len(historical_values)
    historical_std = (sum((x - historical_avg) ** 2 for x in historical_values) / len(historical_values)) ** 0.5

    if historical_std == 0:
        return 0.0

    # Calculate z-score (number of standard deviations from mean)
    surprise = (current_value - historical_avg) / historical_std
    return surprise

async def detect_macro_events(economic_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect significant macro economic events from economic data."""
    macro_events = []

    for indicator in economic_data:
        try:
            # Fetch historical data for comparison
            if indicator.get("source") == "FRED" and indicator.get("series_id"):
                historical_data = await fetch_fred_data(indicator["series_id"], limit=12)  # Last 12 observations

                if historical_data and "historical_values" in historical_data:
                    surprise = calculate_economic_surprise(
                        indicator["value"],
                        historical_data["historical_values"]
                    )

                    # Significant surprise threshold (2+ standard deviations)
                    if abs(surprise) >= 2.0:
                        macro_events.append({
                            "type": "MacroShock" if abs(surprise) >= 2.5 else "MacroRelease",
                            "indicator": indicator["name"],
                            "value": indicator["value"],
                            "surprise": surprise,
                            "magnitude": "High" if abs(surprise) >= 2.5 else "Medium",
                            "direction": "positive" if surprise > 0 else "negative",
                            "date": indicator["date"],
                            "source": indicator["source"]
                        })

        except Exception as e:
            print(f"❌ Error processing macro event for {indicator.get('name', 'unknown')}: {e}")
            continue

    return macro_events

async def fetch_economic_rss_feeds() -> List[Dict[str, Any]]:
    """Fetch economic news from RSS feeds as fallback (no API key required)."""
    economic_feeds = [
        "https://www.federalreserve.gov/feeds/press_all.xml",
        "https://www.bls.gov/feed/news_release/rss.xml",
        "https://www.census.gov/economic-indicators/indicator.xml"
    ]

    economic_events = []

    for feed_url in economic_feeds:
        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:3]:  # Limit to 3 entries per feed
                if hasattr(entry, 'title') and hasattr(entry, 'summary'):
                    title = entry.title.upper()
                    summary = getattr(entry, 'summary', '').upper()
                    text = f"{title} {summary}"

                    # Look for key economic indicators in the text
                    economic_indicators = {
                        "CPI": ["CONSUMER PRICE", "INFLATION", "CPI"],
                        "EMPLOYMENT": ["UNEMPLOYMENT", "JOBS", "PAYROLL", "EMPLOYMENT"],
                        "GDP": ["GDP", "GROSS DOMESTIC", "ECONOMIC GROWTH"],
                        "FED": ["FEDERAL RESERVE", "INTEREST RATE", "MONETARY POLICY"],
                        "HOUSING": ["HOUSING", "HOME SALES", "CONSTRUCTION"]
                    }

                    for category, keywords in economic_indicators.items():
                        for keyword in keywords:
                            if keyword in text:
                                # Extract potential numbers from the text
                                import re
                                numbers = re.findall(r'\d+\.?\d*%?', text)

                                economic_events.append({
                                    "indicator": category,
                                    "title": entry.title,
                                    "date": getattr(entry, 'published', ''),
                                    "source": feed.feed.get('title', 'Economic RSS'),
                                    "numbers": numbers[:3],  # First 3 numbers found
                                    "category": "economic_release"
                                })
                                break
                        if economic_events and economic_events[-1]["indicator"] == category:
                            break

        except Exception as e:
            print(f"❌ Economic RSS feed error for {feed_url}: {e}")
            continue

    return economic_events

async def generate_mock_economic_events() -> List[Dict[str, Any]]:
    """Generate realistic mock economic events when APIs are unavailable."""
    import random

    # Simulate realistic economic data with some volatility
    mock_events = []

    # Only generate events occasionally to simulate real economic calendar
    if random.random() < 0.1:  # 10% chance of economic event
        indicators = [
            {"name": "CPI", "base": 3.2, "volatility": 0.3},
            {"name": "Unemployment Rate", "base": 3.8, "volatility": 0.2},
            {"name": "GDP Growth", "base": 2.5, "volatility": 0.4},
            {"name": "Federal Funds Rate", "base": 5.25, "volatility": 0.25}
        ]

        selected = random.choice(indicators)
        value = selected["base"] + random.uniform(-selected["volatility"], selected["volatility"])

        # Calculate surprise based on deviation from base
        surprise = (value - selected["base"]) / selected["volatility"]

        if abs(surprise) >= 1.0:  # Only significant surprises
            mock_events.append({
                "indicator": selected["name"],
                "value": value,
                "surprise": surprise,
                "magnitude": "High" if abs(surprise) >= 2.0 else "Medium",
                "direction": "positive" if surprise > 0 else "negative",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Simulated"
            })

    return mock_events


# X (Twitter) sentiment analysis using Grok API
async def fetch_x_sentiment_analysis(ticker: str) -> Dict[str, Any]:
    """Fetch and analyze X posts for a ticker using Grok API."""
    if not GROK_API_KEY:
        return {"error": "GROK_API_KEY not available"}

    try:
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROK_API_KEY}"
        }

        prompt = f"""Using your available tools like x_keyword_search or x_semantic_search, fetch the latest 20 posts on X that mention the ticker ${ticker} (sort by Latest mode). Focus on posts from the past 7 days that discuss stock performance, news, or sentiment.

Then, perform the following analysis:

Analyze the overall sentiment of the posts: Categorize them as positive, negative, neutral, or mixed. Provide a sentiment score on a scale of -1 (very bearish) to +1 (very bullish), based on the majority tone.
Determine the overall direction of the stock: Summarize if the consensus points to upward (bullish), downward (bearish), or sideways movement, with key reasons extracted from the posts (e.g., earnings reports, market trends, or events).
If any posts mention or link to a new article (published within the last 7 days), use tools like browse_page or web_search to access and summarize the article. Include the article's title, source, publication date, key points, and how it relates to the stock.
Present your response in a structured format:

Latest Posts Summary: List 5-10 key posts with usernames, dates, and brief excerpts.
Sentiment Analysis: Overall score and breakdown.
Stock Direction: Predicted direction and rationale.
Article Summaries: If applicable, one per mentioned article.
Do not fabricate information; base everything on the searched data."""

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a financial sentiment analyst with access to X (Twitter) data. Use your tools to search for real posts and provide accurate analysis."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": "grok-4-latest",
            "stream": False,
            "temperature": 0.3
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                analysis_text = data["choices"][0]["message"]["content"]

                # Parse the structured response to extract sentiment score
                sentiment_score = extract_sentiment_score(analysis_text)

                return {
                    "ticker": ticker,
                    "analysis": analysis_text,
                    "sentiment_score": sentiment_score,
                    "timestamp": int(time.time()),
                    "source": "X_via_Grok",
                    "token_usage": data.get("usage", {})
                }
            else:
                return {"error": "No response from Grok API"}
        else:
            print(f"❌ Grok API error: {response.status_code} - {response.text}")
            return {"error": f"API error: {response.status_code}"}

    except Exception as e:
        print(f"❌ X sentiment analysis error for {ticker}: {e}")
        return {"error": str(e)}

def extract_sentiment_score(analysis_text: str) -> float:
    """Extract numerical sentiment score from Grok's analysis text."""
    try:
        # Look for sentiment score patterns in the text
        import re

        # Pattern 1: "sentiment score: 0.X" or "score of 0.X"
        score_patterns = [
            r"sentiment score[:\s]+([+-]?\d*\.?\d+)",
            r"score of ([+-]?\d*\.?\d+)",
            r"overall score[:\s]+([+-]?\d*\.?\d+)",
            r"bullish.*?([+-]?\d*\.?\d+)",
            r"bearish.*?([+-]?\d*\.?\d+)"
        ]

        for pattern in score_patterns:
            match = re.search(pattern, analysis_text.lower())
            if match:
                score = float(match.group(1))
                # Ensure score is within -1 to +1 range
                return max(-1.0, min(1.0, score))

        # Pattern 2: Look for qualitative sentiment indicators
        text_lower = analysis_text.lower()

        # Count positive and negative indicators
        positive_indicators = ["bullish", "positive", "optimistic", "upward", "buy", "strong", "growth"]
        negative_indicators = ["bearish", "negative", "pessimistic", "downward", "sell", "weak", "decline"]

        pos_count = sum(1 for word in positive_indicators if word in text_lower)
        neg_count = sum(1 for word in negative_indicators if word in text_lower)

        if pos_count > neg_count:
            return 0.5  # Moderately positive
        elif neg_count > pos_count:
            return -0.5  # Moderately negative
        else:
            return 0.0  # Neutral

    except Exception as e:
        print(f"❌ Error extracting sentiment score: {e}")
        return 0.0  # Default to neutral

# Store cumulative sentiment scores for charting
symbol_sentiment_scores = {symbol: [] for symbol in SUPPORTED_SYMBOLS}

async def update_x_sentiment_scores():
    """Update X sentiment scores for all supported symbols."""
    print("🐦 Updating X sentiment analysis...")

    for symbol in SUPPORTED_SYMBOLS:
        try:
            # Fetch sentiment analysis from Grok
            sentiment_data = await fetch_x_sentiment_analysis(symbol)

            if "error" not in sentiment_data:
                score = sentiment_data.get("sentiment_score", 0.0)
                timestamp = sentiment_data.get("timestamp", int(time.time()))

                # Save full sentiment analysis to Supabase
                await supabase_client.save_sentiment_analysis(symbol, sentiment_data)

                # Add to cumulative scores
                symbol_sentiment_scores[symbol].append({
                    "timestamp": timestamp,
                    "score": score,
                    "analysis": sentiment_data.get("analysis", "")[:200] + "..."  # Truncate for storage
                })

                # Keep only last 100 sentiment scores per symbol
                if len(symbol_sentiment_scores[symbol]) > 100:
                    symbol_sentiment_scores[symbol] = symbol_sentiment_scores[symbol][-100:]

                # Create X sentiment event for CEP
                x_sentiment_event = Event(
                    "XSentiment",
                    key=symbol,
                    ts=timestamp,
                    data={
                        "sentiment_score": score,
                        "source": "X_via_Grok",
                        "analysis_preview": sentiment_data.get("analysis", "")[:100]
                    }
                )

                cep.ingest(x_sentiment_event)
                await broadcast(x_sentiment_event)

                print(f"🐦 X Sentiment {symbol}: {score:.2f}")

                # Generate strong sentiment events
                if abs(score) >= 0.7:
                    strong_sentiment_event = Event(
                        "StrongXSentiment",
                        key=symbol,
                        ts=timestamp,
                        data={
                            "sentiment_score": score,
                            "direction": "bullish" if score > 0 else "bearish",
                            "magnitude": abs(score)
                        }
                    )
                    cep.ingest(strong_sentiment_event)
                    await broadcast(strong_sentiment_event)
                    print(f"🚨 Strong X Sentiment {symbol}: {score:.2f} ({'bullish' if score > 0 else 'bearish'})")

            # Rate limiting - don't overwhelm Grok API
            await asyncio.sleep(10)  # 10 seconds between symbols

        except Exception as e:
            print(f"❌ Error updating X sentiment for {symbol}: {e}")
            continue


@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws.accept()
    async with clients_lock:
        clients.append(ws)
    try:
        while True:
            await ws.receive_text()  # keep alive; ignore content
    except WebSocketDisconnect:
        async with clients_lock:
            try:
                clients.remove(ws)
            except ValueError:
                pass

# ---------- Demo price feed & CEP rules ----------

def next_candle(prev_close: float) -> Dict[str, Any]:
    t = int(time.time())
    drift = random.uniform(-0.2, 0.2)
    o = prev_close
    c = max(1.0, o + drift + random.uniform(-0.4, 0.4))
    h = max(o, c) + random.uniform(0.0, 0.3)
    l = min(o, c) - random.uniform(0.0, 0.3)
    v = random.randint(1000, 5000)
    return {"time": t, "open": round(o,2), "high": round(h,2), "low": round(l,2), "close": round(c,2), "volume": v}

async def price_loop():
    """Live price update loop - fetches latest prices every 60 seconds."""
    print("🔄 Starting live price update loop...")

    while True:
        try:
            # Update prices every 60 seconds (respecting API limits)
            await asyncio.sleep(60.0)

            for symbol in SUPPORTED_SYMBOLS:
                try:
                    # Get latest price data
                    latest_data = await get_latest_price(symbol)

                    if latest_data["price"] > 0 and len(candles[symbol]) > 0:
                        # Create a new candle based on latest price
                        last_candle = candles[symbol][-1]
                        current_time = int(time.time())

                        # Create 1-minute candle
                        new_candle = {
                            "time": current_time,
                            "open": last_candle["close"],
                            "high": max(last_candle["close"], latest_data["price"]),
                            "low": min(last_candle["close"], latest_data["price"]),
                            "close": latest_data["price"],
                            "volume": latest_data.get("volume", 1000)
                        }

                        candles[symbol].append(new_candle)

                        # Keep only last 2000 candles
                        if len(candles[symbol]) > 2000:
                            candles[symbol] = candles[symbol][-2000:]

                        # Broadcast and process through CEP
                        await broadcast(Event("Bar", key=symbol, ts=new_candle["time"], data=new_candle))
                        cep.ingest(Bar(symbol, new_candle["open"], new_candle["high"], new_candle["low"], new_candle["close"], new_candle["volume"]))

                        # Check for breakouts per symbol
                        if len(candles[symbol]) >= 21:
                            hh20 = max(c["high"] for c in candles[symbol][-20:])
                            if new_candle["close"] > hh20:
                                cep.sink.emit(Event("Breakout", key=symbol, ts=new_candle["time"], data={"price": new_candle["close"], "lookback": 20}))

                        print(f"📊 Updated {symbol}: ${latest_data['price']:.2f} ({latest_data.get('changePercent', 0):.2f}%)")

                        # Save updated market data to Supabase every 10 minutes
                        if current_time % 600 == 0:  # Every 10 minutes
                            await supabase_client.save_market_data(symbol, candles[symbol][-10:])

                except Exception as e:
                    print(f"❌ Failed to update {symbol}: {e}")

        except Exception as e:
            print(f"❌ Price loop error: {e}")
            await asyncio.sleep(30)  # Wait before retrying

async def news_loop():
    """Live news fetching loop - checks for new articles every 5 minutes."""
    print("📰 Starting live news monitoring...")
    processed_articles = set()  # Track processed articles to avoid duplicates

    while True:
        try:
            # Fetch news from multiple sources
            all_articles = []

            # Fetch from NewsAPI
            newsapi_articles = await fetch_newsapi_articles()
            all_articles.extend(newsapi_articles)

            # Fetch from Alpha Vantage
            alpha_articles = await fetch_alpha_vantage_news()
            all_articles.extend(alpha_articles)

            # Fetch from RSS feeds as fallback
            rss_articles = await fetch_rss_news()
            all_articles.extend(rss_articles)

            # Process new articles
            new_articles_count = 0
            for article in all_articles:
                # Create unique ID for article
                article_id = f"{article['title'][:50]}_{article.get('publishedAt', '')}"

                if article_id not in processed_articles:
                    processed_articles.add(article_id)

                    # Save article to Supabase
                    await supabase_client.save_news_article(article)

                    # Process each symbol mentioned in the article
                    for symbol in article['symbols']:
                        # Only process if sentiment is strong enough
                        if abs(article['sentiment']) >= 0.3:
                            evt = NewsItem(
                                symbol,
                                sentiment=article['sentiment'],
                                headline=article['title'][:100]
                            )
                            cep.ingest(evt)
                            await broadcast(evt)
                            new_articles_count += 1

                            print(f"📰 News: {symbol} | {article['sentiment']:.2f} | {article['title'][:60]}...")

            if new_articles_count > 0:
                print(f"✅ Processed {new_articles_count} new news items")

            # Clean up old processed articles (keep last 1000)
            if len(processed_articles) > 1000:
                processed_articles.clear()

            # Wait 5 minutes before next check
            await asyncio.sleep(300)

        except Exception as e:
            print(f"❌ News loop error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying

async def macro_loop():
    """Live macro economic data monitoring loop - checks every 30 minutes."""
    print("📊 Starting live macro economic monitoring...")
    processed_events = set()  # Track processed events to avoid duplicates

    while True:
        try:
            # Fetch economic data from multiple sources
            economic_data = await fetch_economic_calendar()
            alpha_data = await fetch_alpha_vantage_economic_data()
            rss_data = await fetch_economic_rss_feeds()
            mock_data = await generate_mock_economic_events()

            # Combine all economic data
            all_economic_data = economic_data + alpha_data + mock_data

            # Log RSS data for monitoring
            if rss_data:
                print(f"📊 Found {len(rss_data)} economic RSS items")

            # Detect significant macro events
            macro_events = await detect_macro_events(all_economic_data)

            # Save economic data to Supabase
            for data in all_economic_data:
                await supabase_client.save_economic_data(data)

            # Process new macro events
            new_events_count = 0
            for event_data in macro_events:
                # Create unique ID for event
                event_id = f"{event_data['indicator']}_{event_data.get('date', '')}"

                if event_id not in processed_events:
                    processed_events.add(event_id)

                    # Create MacroRelease event
                    macro_release = MacroRelease(
                        f"US:{event_data['indicator']}",
                        actual=event_data.get('value', 0),
                        surprise=event_data.get('surprise', 0)
                    )
                    cep.ingest(macro_release)
                    await broadcast(macro_release)
                    new_events_count += 1

                    print(f"📊 Macro: {event_data['indicator']} | Surprise: {event_data.get('surprise', 0):.2f} | {event_data.get('magnitude', 'Medium')}")

                    # Create MacroShock if surprise is significant
                    if event_data.get('magnitude') == 'High':
                        macro_shock = MacroShock(
                            f"US:{event_data['indicator']}",
                            magnitude=abs(event_data.get('surprise', 0))
                        )
                        cep.ingest(macro_shock)
                        await broadcast(macro_shock)
                        print(f"🚨 MacroShock: {event_data['indicator']} | Magnitude: {abs(event_data.get('surprise', 0)):.2f}")

            if new_events_count > 0:
                print(f"✅ Processed {new_events_count} new macro events")

            # Clean up old processed events (keep last 100)
            if len(processed_events) > 100:
                processed_events.clear()

            # Wait 30 minutes before next check (economic data updates infrequently)
            await asyncio.sleep(1800)

        except Exception as e:
            print(f"❌ Macro loop error: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes before retrying


async def x_sentiment_loop():
    """X sentiment analysis loop - updates every 2 hours."""
    print("🐦 Starting X sentiment monitoring...")

    # Wait 2 minutes before first run to let other systems initialize
    await asyncio.sleep(120)

    while True:
        try:
            await update_x_sentiment_scores()
            print("✅ X sentiment analysis complete")

            # Wait 2 hours before next analysis (to respect API limits and costs)
            await asyncio.sleep(7200)  # 2 hours

        except Exception as e:
            print(f"❌ X sentiment loop error: {e}")
            await asyncio.sleep(1800)  # Wait 30 minutes before retrying


# CEP rules

def install_rules():
    # News burst rule - now works across all symbols
    cep.on_sliding_count(
        name="news_burst_pos",
        event_type="NewsItem",
        within_sec=120,
        threshold=3,
        where=lambda n: n.data.get("sentiment", 0) >= 0.6,  # Removed symbol filter to work across all symbols
        emit_type="NewsBurst",
    )
    cep.on_macro_shock(series="US:CPI", surprise_abs_ge=0.3, emit_type="MacroShock")
    cep.on_sequence(
        name="macro_then_breakout",
        first_type="MacroShock", then_type="Breakout",
        within_sec=15*60,
        where_then=lambda m,b: True,
        emit_type="TradeEntryIntent",
    )

    # X sentiment correlation rules
    cep.on_sequence(
        name="strong_sentiment_then_breakout",
        first_type="StrongXSentiment", then_type="Breakout",
        within_sec=30*60,  # 30 minutes
        where_then=lambda s,b: s.key == b.key,  # Same symbol
        emit_type="SentimentConfirmedBreakout",
    )

    # Sentiment divergence detection
    cep.on_sliding_count(
        name="sentiment_price_divergence",
        event_type="XSentiment",
        within_sec=60*60,  # 1 hour window
        threshold=3,
        where=lambda s: abs(s.data.get("sentiment_score", 0)) >= 0.5,
        emit_type="SentimentDivergence",
    )

@app.post("/telemetry")
async def telemetry(events: Dict[str, Any]):
    try:
        os.makedirs(os.path.join("data", "telemetry"), exist_ok=True)
        fn = os.path.join("data", "telemetry", datetime.now(timezone.utc).strftime("%Y%m%d") + ".log")
        with open(fn, "a") as f:
            f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "events": events}) + "\n")
        return JSONResponse(status_code=204, content=None)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.on_event("startup")
async def on_startup():
    print("🚀 Starting CEP Event Dashboard...")
    install_rules()
    print("✅ CEP rules installed")

    # Initialize live data in background to avoid blocking startup
    asyncio.create_task(initialize_live_data())
    asyncio.create_task(price_loop())
    asyncio.create_task(news_loop())
    asyncio.create_task(macro_loop())
    asyncio.create_task(x_sentiment_loop())
    print("✅ Background tasks started (including X sentiment analysis)")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8010)