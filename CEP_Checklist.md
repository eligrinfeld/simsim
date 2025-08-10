# CEP Project Systematic Check-Off List

## **Global Navigation Setup**
- [ ] Add top bar with:
  - [ ] Logo
  - [ ] Symbol selector
  - [ ] Timeframe selector (1m, 5m, 1h, 1d)
  - [ ] Search
  - [ ] Filters (Event type, Impact, Sentiment, Topic)
  - [ ] “Replay” toggle
  - [ ] Settings  
- [ ] Create navigation sections:
  - [ ] Live Dashboard
  - [ ] Ticker Deep-dive
  - [ ] Macro Watch
  - [ ] Event Builder
  - [ ] Replay
  - [ ] Settings

## **Live Dashboard**
- [x] Implement primary chart (TradingView lightweight-charts candlestick)
- [ ] Add subpane toggles: RSI, MACD, Volume
- [x] Implement event tracks:
  - [x] Macro ribbon (CPI/NFP/Rate decisions) — basic pill lane for MacroShock
  - [x] News clusters (bubble visualization) — basic pill lane for NewsBurst
  - [x] Signals lane (CEP outputs: Breakout, NewsBurst, MacroShock, TradeEntryIntent) — pill lane and chart markers
- [x] Build right drawer (on marker click) with:
  - [x] Summary (title placeholder) — minimal JSON details shown
  - [x] “Why it fired” explanation
  - [x] Evidence section (friendly fields per event)
  - [ ] Actions: Explain (AI), Add note, Create alert
- [x] Add filter chips to toggle lanes

## **Ticker Deep-Dive**
- [ ] Chart with RSI/MACD/Volume subpanes
- [ ] Factor cards (Valuation, Growth, Quality, Sentiment)
- [ ] “What changed” drawer
- [ ] Notes & scenario sliders

## **Macro Watch**
- [ ] Macro timeline of releases (day view, surprise/impact)
- [ ] Overlay macro regime band on SPY/sector ETF chart
- [ ] Risk dials with popovers

## **Event Builder**
- [ ] Rule presets (Sequence, Sliding Count, Anomaly)
- [ ] Parameter form (types, windows, thresholds)
- [ ] Preview rules on recent data
- [ ] Test run against symbol/time window
- [ ] Save rule

## **Replay**
- [ ] Add time scrubber
- [ ] Show events in firing sequence
- [ ] Speed controls
- [ ] Step/jump to next/previous event

## **Data Contracts**
- [x] Finalize Candle schema
- [x] Finalize Event schema
- [x] Define CEP output types (Breakout, NewsBurst, MacroShock, TradeEntryIntent)
- [ ] Implement REST endpoints:
  - [x] GET /candles
  - [x] GET /events
  - [x] POST /telemetry
- [x] Implement WebSocket /ws push

## **Component Inventory**
- [ ] **Frontend:**
  - [ ] ChartCanvas
  - [ ] EventTracks (MacroRibbon, NewsClusters, SignalsLane)
  - [ ] MarkerLegend & FilterChips
  - [ ] RightDrawer (EventDetails)
  - [ ] RuleBuilder (PresetSelector, ParamForm, PreviewPane)
  - [ ] ReplayControls
- [ ] **Backend:**
  - [x] PriceFeedAdapter
  - [x] NewsAdapter
  - [x] MacroAdapter
  - [x] CEPCore
  - [x] Broadcaster (WS + backfill)
  - [ ] Storage layer

## **Implementation Plan**
### **Milestone M0 – Realtime POC (1–2 days)**
- [x] Backend: FastAPI app (/candles, /ws, CEP core)
- [x] Simulate bars/news/macro data
- [x] Emit sample CEP events
- [x] Frontend: chart, markers, event tracks, right drawer stub
- [x] Tests: /candles, WS handshake, CEP triggers

### **Milestone M1 – Live Adapters + Resilience (3–5 days)**
- [ ] Bars adapter (WS w/ reconnect)
- [ ] News adapter (NewsAPI+RSS, sentiment scoring)
- [ ] Macro schedule + surprise calc
- [ ] Backfill /events; client reconnect logic

### **Milestone M2 – Rule Builder + Multi-Symbol (3–5 days)**
- [ ] Preset rules with parameters
- [ ] Live preview
- [ ] Multi-symbol support & filtering
- [ ] Event persistence

### **Milestone M3 – Replay + Alerts + Explainability (1–2 weeks)**
- [ ] Replay controls
- [ ] Export/play sessions
- [ ] Alerts (in-app/email)
- [ ] Explain action (LLM)

## **Risks & Mitigations**
- [ ] Plan aggregation/throttling for high event volume
- [ ] Implement reconnect/backfill logic
- [ ] Show source & confidence badges
- [ ] Progressive disclosure UI

## **Open Questions**
- [ ] Decide first target users (retail pro/enthusiast vs internal research)
- [ ] Define minimum viable latency and retention
- [ ] Select preferred data providers to wire first (Alpaca/IBKR; NewsAPI/GDELT; FRED)
- [ ] Determine must-have indicators beyond RSI/MACD/MA (VWAP/ATR bands?)
- [ ] Choose single-asset default or multi-asset overview

## **Next Actions**
- [ ] Confirm M0 scope & UX
- [ ] Approve data contracts
- [x] Scaffold M0 (no live keys) and wire tests
