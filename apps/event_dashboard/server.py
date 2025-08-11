from __future__ import annotations
import asyncio, random, time, uuid, os, json, math, traceback
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
    from supabase import supabase_client
except ImportError:
    # Fallback if supabase module not available
    class MockSupabaseClient:
        enabled = False
        async def get_events(self, **kwargs): return []
        async def save_event(self, **kwargs): pass
    supabase_client = MockSupabaseClient()

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

def MacroRelease(series: str, actual: float, estimate: float) -> Event:
    return Event("MacroRelease", key=series, data={"series": series, "actual": actual, "estimate": estimate, "surprise": actual - estimate})

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
async def get_candles(symbol: str = DEFAULT_SYMBOL):
    if symbol not in candles:
        return JSONResponse([])
    return JSONResponse(candles[symbol][-2000:])


@app.get("/symbols")
async def get_symbols():
    """Get list of supported symbols with current prices."""
    symbols_info = []
    for symbol in SUPPORTED_SYMBOLS:
        if symbol in candles and len(candles[symbol]) > 0:
            latest = candles[symbol][-1]
            symbols_info.append({
                "symbol": symbol,
                "price": latest["close"],
                "change": latest["close"] - latest["open"],
                "volume": latest["volume"]
            })
        else:
            symbols_info.append({"symbol": symbol, "price": 0, "change": 0, "volume": 0})
    return JSONResponse(symbols_info)

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

        return {
            "symbol": symbol,
            "price": info.get('currentPrice', info.get('regularMarketPrice', 0)),
            "change": info.get('regularMarketChange', 0),
            "changePercent": info.get('regularMarketChangePercent', 0),
            "volume": info.get('regularMarketVolume', 0),
            "timestamp": int(time.time())
        }
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


# Live news fetching functions
NEWS_API_KEY = os.getenv("NEWS_API_KEY")  # Get from newsapi.org
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")  # Get from alphavantage.co

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
    while True:
        await asyncio.sleep(random.uniform(45, 75))
        est = random.uniform(0.0, 0.4)
        act = est + random.choice([-0.5, -0.3, +0.3, +0.5])
        evt = MacroRelease("US:CPI", actual=act, estimate=est)
        cep.ingest(evt)
        await broadcast(evt)

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
    print("✅ Background tasks started")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8010)