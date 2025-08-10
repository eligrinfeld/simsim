# Product/UI Plan: Interactive, Informative Stock Analysis


## Status (last updated: 2025-08-10)
Legend: [x] done, [~] partial, [ ] not started

### MVP Polish
- [x] TL;DR card with “what changed” deltas (▲/▼, labels) and chip showing last review date
- [x] Factor scorecards: Explain drawer via GPT‑5 with data grounding; static recipe + Inputs table; robust fallback
- [x] Sector percentile badges (heuristic) with tooltip meta (source + as‑of)
- [x] Sparklines: RSI sparkline; lightweight mini‑visuals for Valuation/Growth/Quality
- [x] Scenario sliders (valuation/sentiment weights) with instant recompute and per‑ticker persistence
- [x] Per‑ticker state: last analysis, last tab, notes; scenario sliders persisted
- [x] Macro: Regime and Market Risk dials with detail popovers; Sentiment dial; 30‑day sentiment sparkline; color thresholds; price overlay
- [x] Peers: radar vs peers average (Val/Grow/Qual/Sent) + compact table; static peer set for common tickers
- [x] News timeline with topic chips, daily grouping, and source badges
- [x] TL;DR drivers copy polish; source badges (AlphaV, Finnhub)
- [x] Link‑outs to detailed sources from TL;DR and Factor cards

### Phase 2
- [~] Peer radar + percentile tables (basic table present; needs true sector percentiles and filters)
- [x] Macro regime strip (dials present) + lite overlay on price chart
- [ ] Sentiment clustering view (timeline bubbles/clusters)
- [ ] Alerts/digests; watchlist with notes & review cadence (notes done; watchlist/alerts pending)

### Phase 3
- [ ] Valuation sandbox (multiples & DCF) and macro “what‑if” toggles
- [ ] Confidence modeling per factor; uncertainty badges surfaced
- [ ] PDF export and shareable snapshot links

### Acceptance Criteria (MVP)
- [x] Overview shows verdict, drivers, and change chips
- [~] Each factor has sparkline, percentile vs sector, and Explain drawer (RSI sparkline; mini‑visuals for others until fundamentals history added)
- [x] News tab shows timeline, topic filters, open headlines in new tab
- [x] Scenario sliders instantly recompute final score
- [x] State is persisted per ticker and restored on revisit

### Open Technical TODOs
- Real sector percentile distributions (nightly precompute) to replace heuristics; file‑based stub in place and wiring added
- Cache AI explanations per (symbol,factor) with TTL to cut cost/latency
- Improve error surfacing in UI for failed AI/macro calls
- Analytics instrumentation for interactions (Explain, What‑Changed, Scenarios) — client hooks in place; consider backend endpoint
- Add unit/integration tests for /analyze, /explain, and macro/news endpoints — initial tests added

### Next Up (this sprint)
1) Sector percentiles: simple file‑based ingest; display sector when present; add tests for percentiles_meta.source toggle
2) Analytics: optionally post client events to a /telemetry endpoint (stub)
3) Tests: extend /explain (happy path) and /news proxy (happy path), and broader /analyze shape assertions
4) Minor UI polish: news item time badges and hover details on peers radar

### Realtime Event‑Aware Chart (POC)
Goal: Add a lightweight-charts dashboard that streams prices and overlays CEP-derived events (Breakout, NewsBurst, MacroShock, TradeEntryIntent) in real time.

- Scope (first iteration)
  - FastAPI app with WebSocket push and /candles seed endpoint
  - Minimal CEP core (sequence, sliding count, macro shock) in-process
  - Frontend at public/index.html using TradingView lightweight-charts via CDN
  - Simulated bars + simple rules; hooks to swap in real feeds later
- Integration options
  - New app: apps/event_dashboard/server.py + public/index.html (recommended for decoupling)
  - Or add WS + static route under apps/stock_analyzer (bigger single file)
- Data hooks (later iterations)
  - Bars: broker/data WS adapter → cep.ingest(Bar(...)) + broadcast(Event("Bar", ...))
  - News: pipe macro_sentiment_api /news into cep.ingest(NewsItem(...))
  - Macro: pipe scheduled macro prints into cep.ingest(MacroRelease(...))
- Acceptance (POC)
  - Candlesticks stream at 1s tick; markers appear for derived events
  - WebSocket reconnects gracefully; initial /candles load ≤2000 rows
  - Basic unit tests: /candles returns seed; WS handshake; CEP rule emits on synthetic feed
- Next steps
  - Subpanes (RSI/volume), topic filters, multi-symbol support
  - Event persistence (Done via Supabase)
  - Next: Replay controls + Multi-symbol + Auth/RLS tighten


## Objectives
- Reduce cognitive load with a clear TL;DR and progressive disclosure
- Make scores explainable (why/what changed), not just numbers
- Enable exploration via what‑if controls and scenario toggles
- Show trends and deltas over time to build intuition
- Create continuity with watchlists, notes, and alerts

## Information Architecture (IA)
- Overview (TL;DR)
  - Verdict + conviction, key drivers, since‑last‑review changes
- Fundamentals
  - Quality, Growth, Valuation, Margins with sector‑relative context
- Technicals
  - Trend/momentum, key levels, regime detection, recent signals
- Sentiment / News
  - Timeline and clusters, aggregated scores, topics, headline links
- Macro / Risk
  - Macro regime strip, market risk dials, relevant series overlays
- Peers & Benchmarks
  - Comparables, percentile ranks, sector/industry filters
- Portfolio Impact (if held)
  - Contribution to risk/return, alternatives
- Scenarios / Sandbox
  - Weight sliders, valuation sensitivity, macro toggles

## High‑Impact UI Patterns
- TL;DR Card
  - Verdict (Buy/Hold/Avoid) + conviction badge
  - 2–4 bullet drivers (e.g., “Valuation stretched; sentiment cooling; trend intact”)
  - “Since last review” chip: “Valuation +1, Sentiment −2, Price +4.1%”
- Factor Scorecards
  - Current score, 12m sparkline, sector percentile, “why” tooltip
  - “Explain this score” drawer with thresholds, inputs, links to sources
- Contribution Bar (Waterfall)
  - Horizontal stacked bar showing each factor’s contribution to final score
- Confidence/Uncertainty Indicators
  - Per‑factor data freshness/completeness/volatility → confidence (High/Med/Low)
- “What Changed?” Diff View
  - Compare Now vs Last week/month across metrics, scores, price, headlines
  - Color‑coded deltas with ▲▼ magnitude badges
- News Timeline + Clustering
  - Bubble timeline (size=coverage, color=sentiment), topic chips, filters
  - Cluster click → representative headlines; “Open sources” links
- Macro Regime Strip
  - Dials: CPI YoY, Unemployment, 10y–2y, Policy Rate, Recession proxy
  - Badge: “Macro regime: Late cycle (Neutral−)”
- Technicals Interactions
  - Toggles: MA50/200, RSI, MACD, volume profile; key level bands; “test count”
  - Quick “If price −5%/+5%” buttons to see factor sensitivity
- Peer Comparison
  - Radar/spider (Quality/Growth/Valuation/Sentiment) vs peers; percentile table
- Scenario Sandbox
  - Sliders: factor/sentiment/macro weights; valuation multiples/DCF knobs
  - Macro toggles: yield curve normalization, CPI −1pp → impact on score/decision

## Interactions That Increase Stickiness
- Watchlist + Notes
  - Personal thesis, price alerts, review cadence (weekly/monthly)
  - Rules: “Alert if sentiment < −0.2 for 3 days” or “PE > 35”
- Digest & Alerts
  - Daily/weekly digest: “3 tickers changed verdict; 2 price alerts triggered”
  - “Only material changes” threshold to reduce noise
- Keyboard & Quick Actions
  - Shortcuts: g o (Overview), g n (News), / (Search)
  - Action bar: Export PDF, Share snapshot, Add note, Set alert
- Personalization & Presets
  - Weight presets (Value, Momentum‑leaning); save custom layouts; dark/light mode

## Data Storytelling & Explainability
- Factor “Recipe” Popover
  - Show formula, inputs, thresholds (e.g., “RSI 69.9 → 4/5; 70+ capped unless trend strong”)
- Source Transparency
  - Timestamps per data type; provider badges (Alpha Vantage, Finnhub, FRED); article links
- Uncertainty Language
  - “Confidence Medium: fundamentals current, sentiment mixed, macro neutral”
  - “Data gap” ribbons when inputs missing; suggest refresh actions

## Helpful Visualizations
- Score Waterfall: neutral → bars up/down per factor → final score
- Sentiment River: positive vs negative volume and net score over 30–90 days
- Macro vs Ticker: overlay regime periods on price to show sensitivity
- Relative Valuation Heatmap: P/E, EV/EBITDA, P/S vs sector percentiles

## Modes by User Level
- Beginner Mode: fewer toggles, plain‑English tooltips, “What does this mean?” prompts
- Advanced Mode: full overlays, export raw data, custom weighting, indicator params

## Performance & UX Polish
- Progressive rendering: TL;DR first, then charts/news
- Skeleton loaders; optimistic UI for refresh
- Prefetch peers and headlines for fast tab switches
- Cache last N analyses per ticker for instant compare

## Privacy, Trust, Safety
- API quota/status banners; graceful degradation with messages
- Clear disclaimers and methodology links
- Anonymized logging, opt‑out toggle

## MVP → Phase Roadmap
- MVP Polish (2–3 sprints)
  - TL;DR card with “what changed” deltas
  - Factor scorecards with “Explain” tooltips/drawers
  - News timeline with topic chips and source links
  - Scenario weight sliders (factor/sentiment/macro)
- Phase 2 (2–3 sprints)
  - Peer radar + percentile tables; sentiment clustering view
  - Macro regime strip + overlay on price chart
  - Alerts/digests; watchlist with notes & review cadence
- Phase 3 (3–4 sprints)
  - Valuation sandbox (multiples & DCF) and macro “what‑if” toggles
  - Confidence modeling per factor; uncertainty badges surfaced
  - PDF export and shareable snapshot links

## Acceptance Criteria (MVP)
- Overview shows verdict, conviction, 3 drivers, and change chips within 1.5s
- Each factor card has sparkline, percentile vs sector, and working Explain drawer
- News tab displays timeline, topic filters, and opens headlines in new tab
- Scenario sliders instantly recompute final score (<250ms perceived)
- State is persisted per ticker (last analysis, notes) and restored on revisit

## Technical Notes & Components
- Components:
  - TLDRCard, ChangeChips, FactorCard, ExplainDrawer, ContributionWaterfall
  - NewsTimeline, TopicChips, ClusterPopover
  - MacroStrip, RiskDials, PeerRadar, PercentileTable
  - ScenarioPanel (sliders), WeightPresetSelector
- Data layer:
  - Cache + last‑analysis snapshots per ticker
  - Lightweight diff engine to compute deltas since last snapshot
- Performance:
  - Precompute sector percentiles nightly; memoize indicator windows
  - Virtualized lists for news; defer heavy charts below fold

## Success Metrics
- Time‑to‑insight (TTI) from page load to verdict understood < 10s (p95)
- Interaction rate with Explain/What‑Changed > 35%
- Repeat weekly usage for watchlist users > 50%
- Alert precision (user‑kept alerts without disabling) > 70%

## Risks & Mitigations
- Data inconsistency → show timestamps/provider badges; stale warnings
- Alert fatigue → materiality thresholds + bundled digests
- Over‑complex UI → Beginner mode + presets; progressive disclosure

## Next Steps
1) Confirm MVP scope and success metrics
2) Wireframe TL;DR, Factor Card + Explain, News Timeline, Scenario Panel
3) Define data contracts for deltas, percentiles, and scenario recompute
4) Implement MVP in feature‑flagged path; instrument analytics
5) Dogfood with internal watchlist; iterate before public release

