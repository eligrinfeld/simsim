# Aladdin-ish Open Platform (Starter)

See prd.md for the machine-readable build plan.


## Quickstart
- make setup
- make run-pipeline
- make test

## Data API endpoints
- GET /health
- GET /prices?ticker=AAPL&start=2024-01-01&end=2025-01-01
- GET /macro?series_id=UNRATE&observation_start=2020-01-01&ttl_seconds=86400
  - Use refresh=true to bypass cache; responses cached under data/macro/
- GET /fundamentals?ticker=AAPL
  - Requires SEC_API_KEY; returns recent 10-K/10-Q metadata via sec-api

## Environment
Create .env with your keys:
- FRED_API_KEY=...
- SEC_API_KEY=...

## Artifacts
Pipeline writes:
- data/prices.(parquet|csv)
- signals/factor.(parquet|csv), signals/final.(parquet|csv)
- portfolio/weights.(parquet|csv)
- risk/report.json (with vol, MDD, VaR, CVaR)
- backtests/equity_curve.csv
Mirrored under artifacts/run_YYYYMMDD/
