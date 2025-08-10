# Stock Analysis Assistant

Personal web app for individual stock analysis with AI-powered recommendations.

## Features
- Enter stock ticker → auto-fetch fundamentals & technicals
- 1-5 scale factor scoring with AI explanations
- Buy/Hold/Avoid recommendations with reasoning
- Historical price charts with technical indicators
- Save analyses for comparison over time

## Data Sources
- Alpha Vantage: prices, basic technicals
- Finnhub: fundamentals, news, analyst estimates
- pandas-ta: local indicator calculations

## Usage
```bash
cd apps/stock_analyzer
uvicorn app:app --reload
# Visit http://localhost:8000
```

## API Endpoints
- GET /analyze?ticker=AAPL - Full stock analysis
- GET /history/{ticker} - Past analyses
- POST /override - Manual score override
