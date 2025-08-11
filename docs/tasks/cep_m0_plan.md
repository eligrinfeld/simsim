# CEP Milestone M0 — Realtime POC

Scope
- FastAPI app with /candles seed and /ws push
- Minimal CEP: sliding count (NewsBurst), macro shock (MacroShock), sequence (MacroShock→Breakout)
- Simulated feeds (bars, news, macro); hooks for live adapters
- Frontend: lightweight-charts, markers, event tracks (macro/news/signals), drawer stub
- Tests: /candles returns seed; WS handshake; CEP emits on synthetic triggers

Tasks
1) App scaffold [backend]
   - Create apps/event_dashboard/server.py (FastAPI, StaticFiles public/, WS, /candles)
   - In-memory state: candles[], clients[], CEP core
   - Broadcast loop and CEP sink subscription
2) Frontend scaffold [frontend]
   - public/index.html with chart, markers, event tracks, WS client
   - Fetch /candles for initial seed; render markers on events
3) CEP rules [backend]
   - on_sliding_count for NewsBurst (≥3 pos in 2m)
   - on_macro_shock for CPI surprise ≥0.3
   - on_sequence MacroShock then Breakout within 15m
4) Simulated feeds [backend]
   - price_loop: 1s candles; breakout detect against hh20
   - news_loop: random positive/negative every 7–12s
   - macro_loop: surprise every 45–75s
5) Tests [tests]
   - test_candles_seed: GET /candles returns list of dicts with OHLC
   - test_ws_handshake: connect /ws and receive Bar within timeout
   - test_cep_emit: drive rule with synthetic events and expect emit
6) Dev tooling [repo]
   - Makefile target run-event-dashboard
   - README snippet under apps/event_dashboard/README.md

Exit criteria
- App runs: `uvicorn apps.event_dashboard.server:app` and shows live markers
- All tests pass
- No external keys required

