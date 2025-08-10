# Aladdin-ish Open Platform (Starter)

See prd.md for the machine-readable build plan.


## Quickstart
- make setup
- make run-pipeline
- make test

## Dashboard
- streamlit run apps/dashboard/app.py
- Navigate: Overview, Universe, Signals, Portfolio, Risk, Backtests

## Services
- Data API: uvicorn services.data_api.app:app --host 127.0.0.1 --port 8080
- Sentiment API: uvicorn services.sentiment_api.app:app --host 127.0.0.1 --port 8082
- Macro Sentiment API: uvicorn services.macro_sentiment_api.app:app --host 127.0.0.1 --port 8001

## Stock Analysis Assistant
- Personal stock analysis with AI recommendations
- cd apps/stock_analyzer && uvicorn app:app --host 127.0.0.1 --port 8000
- Visit http://localhost:8000 for web interface
- Features: 1-5 scale factor scoring, macro/sentiment integration, Buy/Hold/Avoid decisions

## Data API endpoints
- GET /health
- GET /prices?ticker=AAPL&start=2024-01-01&end=2025-01-01
- GET /macro?series_id=UNRATE&observation_start=2020-01-01&ttl_seconds=86400
  - Use refresh=true to bypass cache; responses cached under data/macro/
- GET /fundamentals?ticker=AAPL
  - Requires SEC_API_KEY; returns recent 10-K/10-Q metadata via sec-api

## Environment
Create .env with your API keys for live data:
- **FRED_API_KEY**=... (for live macro data - get free at https://fred.stlouisfed.org/docs/api/api_key.html)
- **SEC_API_KEY**=... (for SEC filings - get free at https://sec-api.io/)
- **ALPHAVANTAGE_API_KEY**=... (for live stock prices - get free at https://www.alphavantage.co/support/#api-key)
- **FINNHUB_API_KEY**=... (for live fundamentals - get free at https://finnhub.io/register)
- **NEWS_API_KEY**=... (for live news sentiment - get free at https://newsapi.org/ - 1000 requests/day)

**News Integration Features:**
- **With NEWS_API_KEY**: Live news articles from NewsAPI.org + Google News RSS
- **Without NEWS_API_KEY**: Google News RSS only (free, no key required)
- **Enhanced Sentiment**: Advanced keyword analysis with weighted scoring
- **Geopolitical Detection**: Flags articles with geopolitical content

**Without API keys**: System gracefully falls back to enhanced realistic dummy data.
**With API keys**: System uses live market data for real-time analysis.

## Artifacts
Pipeline writes:
- data/prices.(parquet|csv)
- signals/factor.(parquet|csv), signals/final.(parquet|csv)
- portfolio/weights.(parquet|csv)
- risk/report.json (with vol, MDD, VaR, CVaR)
- backtests/equity_curve.csv
Mirrored under artifacts/run_YYYYMMDD/
