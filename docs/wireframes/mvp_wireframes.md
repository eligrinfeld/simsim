# MVP Wireframes (Annotated)

This document outlines low-fidelity wireframes for the MVP UI improvements: Overview (TL;DR), Factor Cards + Explain, News Timeline, and Scenario Panel. Each section includes layout, interactions, and data requirements.

---

## 1) Overview (TL;DR)

Layout (desktop)

[ Header ]  [ Search Ticker | Watchlist | Settings ]

+-------------------------------------------------------------+
|  TL;DR Card                                                 |
|  ┌───────────────────────────────────────────────────────┐  |
|  | Verdict:  Hold  | Conviction: Medium                 |  |
|  | Key Drivers:                                         |  |
|  |  • Valuation stretched; • Sentiment cooling;         |  |
|  |  • Trend intact                                       |  |
|  | Since Last Review:  Valuation ▲ +1 | Sentiment ▼ −2  |  |
|  | Price Δ: +4.1% in 14d                                 |  |
|  └───────────────────────────────────────────────────────┘  |
|                                                             |
|  Contribution Waterfall (to final score)                    |
|  [   Quality ++ | Growth + | Valuation −− | Sentiment −  ]  |
|                                                             |
|  Quick Links:  Explain methodology • Export PDF • Set alert |
+-------------------------------------------------------------+

Key interactions
- Click "Since Last Review" to open Diff Drawer (what changed by factor & inputs)
- Hover segments on Contribution Waterfall → shows factor points and inputs
- Export snapshot (PDF) and copy shareable link (internal)

Data required
- Current verdict + confidence
- Factor scores (0–5), final score, point contributions
- Delta since last snapshot (factor + input deltas)

---

## 2) Factor Cards with Explain Drawer

Grid of cards (2–3 per row)

┌──────── Factor: Valuation (3/5) ────────┐   ┌──────── Factor: Trend (4/5) ─────┐
│  Percentile vs sector: 62nd             │   │  Above MA200, RSI 69.9           │
│  Sparkline 12m:  ▄▅▆█▆▅▃                │   │  Sparkline 12m:  ▂▃▅▆█           │
│  Status: Expensive vs history/peers     │   │  Status: Trend intact, overbought│
│  [Explain] [View Inputs]                │   │  [Explain] [View Inputs]         │
└─────────────────────────────────────────┘   └──────────────────────────────────┘

Explain Drawer (opens from right)
- Title: "Valuation score 3/5 — why?"
- Recipe: thresholds and rules applied
  - P/E 33.6 → bucket: "High" (−1)
  - EV/EBITDA 22.1 → bucket: "Elevated" (−1)
  - P/S 8.9 → bucket: "High" (−1)
  - Sector percentile 62% → neutral (0)
  - Net contribution: −2 points from neutral → score 3/5
- Inputs table with timestamps and providers (Finnhub)
- Link: "Compare vs peers" → Peers tab with valuation heatmap

Interactions
- Hover sparkline → shows mini-tooltip with last 5 points
- View Inputs → modal with raw values & last updated

---

## 3) News Timeline + Topics

Layout

+-------------------------------------------------------------+
| Filters:  Time: 7d ▾  | Topics: [earnings] [guidance] [+]   |
| Sources: [All] [NewsAPI] [Google RSS]                       |
|                                                             |
| Timeline: (bubble = article cluster; color = sentiment)     |
|  •   •     ●●    ○○○      ●     ●●●                         |
|                                                             |
| Cluster click → Popover:                                    |
|  - Representative headline                                  |
|  - Avg sentiment, article count, sources                    |
|  - Buttons: [Open articles] [Copy links]                    |
+-------------------------------------------------------------+

Sidebar (right)
- Top Headlines (latest 10)
  1) Title (source) — sentiment chip (+/−)
  2) …
- Topic chips with counts (Earnings, Product, Regulation, Macro)

Interactions
- Filter by time window & topics; updates timeline and list
- Hover cluster → shows date range & avg sentiment
- Click "Open articles" → opens links in new tabs

Data required
- Articles with: title, url, published_at, source, topic (heuristic tag), sentiment
- Clustered groups by time and similarity (MVP: time‑bucketed only)

---

## 4) Scenario Panel (What‑if)

Right drawer / bottom panel

┌──────── Scenarios ────────┐
│ Presets: Value | Balanced | Momentum                        │
│ Factor Weights                                              │
│  Quality  [====|---]  20%                                  │
│  Growth   [===-|---]  20%                                  │
│  Valuation[==--|---]  25%                                  │
│  Sentiment [=---|---] 15%                                  │
│  Macro     [=---|---] 20%                                  │
│                                                          (i)│
│ Sentiment Emphasis  [--|------]                            │
│ Macro Tilt          [----|----]                            │
│                                                          (i)│
│ Quick: Price −5% | Price +5%                               │
│ Result: Final score 62% → 66%  (Δ +4%)                     │
│ [Apply] [Reset]                                            │
└───────────────────────────┘

Interactions
- Sliders update final score instantly (<250ms perceived)
- Quick buttons simulate immediate price moves; reflect in technical score
- Presets load stored weight sets; "Apply" persists to user profile

Data required
- Current factor scores + recompute function with new weights
- Local persistence of chosen preset/weights

---

## Responsive & Accessibility Notes
- Mobile: collapse grids to single column; Scenario Panel as bottom sheet
- Keyboard: shortcuts (g o, g n, /), tab order logical, focus states visible
- Color: sentiment red/green with color‑blind safe palette; icons + labels, not color alone

## Technical Components (mapping)
- TLDRCard, ChangeChips, ContributionWaterfall
- FactorCard, ExplainDrawer, InputsModal
- NewsTimeline, TopicChips, HeadlinesList, ClusterPopover
- ScenarioPanel, WeightPresetSelector

## Open Questions (to confirm)
- Do we store per‑user presets or global presets only (MVP: local/user)?
- Minimum time windows for news (7/14/30d) — default 7d?
- Export format preference: PDF vs image + data bundle?

