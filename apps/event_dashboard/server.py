from __future__ import annotations
import asyncio, random, time, uuid, os, json
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Deque, Dict, List, Optional
from collections import defaultdict, deque
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

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
app.mount("/static", StaticFiles(directory="apps/event_dashboard/public"), name="static")

@app.get("/")
async def index():
    # Serve the SPA index
    return StaticFiles(directory="apps/event_dashboard/public").lookup_path("index.html")[0]


SYMBOL = "SPY"
candles: List[Dict[str, Any]] = []
clients: List[WebSocket] = []
clients_lock = asyncio.Lock()

# Keep a small backfill buffer of recent non-Bar events
RECENT_MAX = 500
recent_events: Deque[Dict[str, Any]] = deque(maxlen=RECENT_MAX)

cep = CEP()

async def broadcast(evt: Event):
    msg = {"type": evt.type, "key": evt.key, "ts": int(evt.ts), "data": evt.data}
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
cep.sink.subscribe(lambda e: asyncio.create_task(broadcast(e)))

@app.get("/candles")
async def get_candles(symbol: str = SYMBOL):
    return JSONResponse(candles[-2000:])

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
    # seed
    base = 450.0
    last = base
    for _ in range(200):
        k = next_candle(last); last = k["close"]; candles.append(k)
    while True:
        await asyncio.sleep(1.0)
        k = next_candle(candles[-1]["close"])
        candles.append(k)
        await broadcast(Event("Bar", key=SYMBOL, ts=k["time"], data=k))
        cep.ingest(Bar(SYMBOL, k["open"], k["high"], k["low"], k["close"], k["volume"]))
        if len(candles) >= 21:
            hh20 = max(c["high"] for c in candles[-20:])
            if k["close"] > hh20:
                cep.sink.emit(Event("Breakout", key=SYMBOL, ts=k["time"], data={"price": k["close"], "lookback": 20}))

async def news_loop():
    headlines_pos = ["Analyst upgrade", "Buyback announced", "Strong sector flows"]
    headlines_neg = ["Regulatory probe", "Guidance cut", "Industry strike risk"]
    while True:
        await asyncio.sleep(random.uniform(7, 12))
        sent = random.choice([+0.7, +0.8, -0.7, -0.8])
        hl = random.choice(headlines_pos if sent > 0 else headlines_neg)
        evt = NewsItem(SYMBOL, sentiment=sent, headline=hl)
        cep.ingest(evt)
        await broadcast(evt)

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
    cep.on_sliding_count(
        name="news_burst_pos",
        event_type="NewsItem",
        within_sec=120,
        threshold=3,
        where=lambda n: n.data.get("sentiment", 0) >= 0.6 and n.key == SYMBOL,
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

@app.on_event("startup")

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

async def on_startup():
    install_rules()
    asyncio.create_task(price_loop())
    asyncio.create_task(news_loop())
    asyncio.create_task(macro_loop())


