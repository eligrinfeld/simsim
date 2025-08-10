## Wireframe map (concise)

### Global navigation
- Top bar: Logo • Symbol selector • Timeframe (1m, 5m, 1h, 1d) • Search • Filters (Event type, Impact, Sentiment, Topic) • “Replay” toggle • Settings
- Sections:
  - Live Dashboard (default)
  - Ticker Deep‑dive
  - Macro Watch
  - Event Builder
  - Replay
  - Settings

### Live Dashboard
- Primary canvas
  - Candlestick chart (TradingView lightweight‑charts)
  - Subpane toggles: RSI, MACD, Volume (expand/collapse)
- Event tracks (stacked under the chart, horizontally aligned with time scale)
  - Macro ribbon: CPI/NFP/Rate decisions (color by surprise/impact)
  - News clusters: bubbles (size=coverage, color=sentiment), tooltips show headlines count and avg sentiment
  - Signals lane: CEP outputs (Breakout, NewsBurst, MacroShock, TradeEntryIntent)
- Right drawer (opens on marker click)
  - Summary: Title, impact, confidence badge, timestamp, source badges
  - Why it fired: rule path, inputs, thresholds
  - Evidence: headline list (for NewsBurst), macro print vs estimate (for MacroShock), indicator snapshot (for Breakout)
  - Actions: Explain (AI), Add note, Create alert from this pattern
- Legend (footer of chart)
  - Markers/color mapping; filter chips to hide/show layers quickly

### Ticker Deep‑dive
- Chart with subpanes (RSI/MACD/Volume)
- Factor cards: Valuation, Growth, Quality, Sentiment with percentiles and sparklines
- “What changed” drawer; notes; scenario sliders

### Macro Watch
- Macro timeline: releases by day with surprise/impact
- Overlay macro regime band on SPY/sector ETF chart
- Risk dials with popovers

### Event Builder
- Rule presets: Sequence, Sliding Count, Anomaly
- Parameter form: types, windows, thresholds; preview on recent data
- Test run against symbol/time window; save rule

### Replay
- Scrubber across day/week
- Plays events in sequence; markers appear as they “fire”
- Speed controls; step events; jump to next/prev event

---

## Data contracts (initial)

- Candle (REST /candles, WS)
  - { time: number(unix), open: number, high: number, low: number, close: number, volume?: number }
- Event (WS)
  - { type: string, ts: number(unix), id: string, key: string(symbol/series), data: object, impact?: "low"|"med"|"high", confidence?: number(0..1), source?: string }
- CEP output types (examples)
  - Breakout: { price: number, lookback: number }
  - NewsBurst: { count: number, window_sec: number, avg_sentiment: number }
  - MacroShock: { series: "US:CPI", surprise: number, actual?: number, estimate?: number }
  - TradeEntryIntent: { rule: string, first: Event, then: Event }
- REST
  - GET /candles?symbol=SPY → Candle[]
  - GET /events?symbol=SPY&since=ts&types=… → Event[] (optional for backfill/reconnect)
  - POST /telemetry → 204 (client analytics)
- WebSocket
  - /ws (server → client push): Bar, and derived Event messages

---

## Component inventory

- Frontend
  - ChartCanvas (candles + markers + subpane toggles)
  - EventTracks (MacroRibbon, NewsClusters, SignalsLane)
  - MarkerLegend, FilterChips
  - RightDrawer (EventDetails: Why, Evidence, Actions)
  - RuleBuilder (PresetSelector, ParamForm, PreviewPane)
  - ReplayControls (Play/Pause, Speed, Step, Jump)
- Backend
  - PriceFeedAdapter (simulated/live)
  - NewsAdapter (NewsAPI/GDELT/RSS)
  - MacroAdapter (FRED/schedule)
  - CEPCore (rules: sequence, sliding count, macro shock, breakout)
  - Broadcaster (WS fanout + /events backfill)
  - Storage (optional v1: ClickHouse/Timescale; v0: in‑memory + JSON logs)

---

## Implementation plan (phased)

- Milestone M0: Realtime POC (1–2 days)
  - Server: FastAPI app with /candles, /ws, CEP core; simulated bars/news/macro; emit 3–4 CEP events
  - Frontend: lightweight‑charts; markers; macro/news/signals tracks; right drawer stub
  - Tests: /candles returns data; WS handshake; CEP emits on synthetic triggers
- Milestone M1: Live adapters + resilience (3–5 days)
  - Bars adapter (broker/data WS) with reconnect; coalesce micro‑events
  - News adapter (NewsAPI+RSS), sentiment scoring (VADER/FinBERT proxy)
  - Macro schedule + prints; surprise calculation
  - Backfill /events; client reconnect with since_ts
- Milestone M2: Rule builder v1 + multi‑symbol (3–5 days)
  - Preset rules with parameters; live preview
  - Partition CEP by key; multi‑symbol charts and tracks; filters per symbol
  - Persist events to storage (append‑only)
- Milestone M3: Replay + alerts + explainability (1–2 weeks)
  - Replay controls; export/play sessions
  - Alerts (in‑app/email) with digest mode
  - Explain action (LLM) showing rule inputs/thresholds and suggested follow‑ups

---

## Risks and mitigations
- Volume of events → aggregate markers, cluster news, throttle WS
- Reconnect gaps → /events backfill; idempotent event IDs
- Data quality → show source badges, timestamps; confidence badge
- Complexity creep → progressive disclosure; defaults/presets; one‑click hide tracks

---

## Open questions
- First target users (retail pro/enthusiast vs internal research)?
- Minimum viable latency and retention?
- Preferred data providers to wire first (Alpaca/IBKR; NewsAPI/GDELT; FRED)?
- Must‑have indicators beyond RSI/MACD/MA (VWAP/ATR bands)?
- Single‑asset default or multi‑asset overview?

---

## Next actions (recommended)
- Confirm the M0 scope and UX (above), pick integration path:
  - Separate app apps/event_dashboard with server.py + public/index.html
- Approve the data contracts and event schema
- I’ll then scaffold M0 (no live keys required) and wire basic tests


