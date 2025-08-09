# Product Requirements Document — Aladdin-ish Open Platform

## 0. What is a Monorepo?
A **monorepo** is a single repository holding multiple services/packages/apps. Benefits: atomic cross-cutting changes, shared tooling (lint/test/CI), and easier discovery. We mitigate downsides (size/ownership) with clear module boundaries, optional submodules, and a single-source-of-truth design to avoid duplication.

## 1. Overview
Open-source, modular, AI-driven market analysis & portfolio management platform (Aladdin-like): data → features/factors → sentiment → signals → optimization & risk → backtest/live → dashboard.

## 2. Git Clone & Setup
```bash
git clone https://github.com/YOUR-ORG/aladdinish-open-platform.git
cd aladdinish-open-platform

# Optional integrated projects as submodules
git submodule add https://github.com/The-Swarm-Corporation/Open-Aladdin integrations/open_aladdin
git submodule add https://github.com/alihassanml/agentic-ai-stock-analysis integrations/agentic_ai_stock_analysis
git submodule add https://github.com/AI4Finance-Foundation/FinRL integrations/finrl
git submodule update --init --recursive

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-quant.txt -r requirements-llm.txt
cp .env.example .env
```

## 3. Architecture
| Layer | Path | Integrations | Purpose |
|------|------|--------------|---------|
| Data Ingestion | services/data_api | OpenBB via openbb_bridge, yfinance, FRED | Unified API, normalized outputs |
| OpenBB Boundary | services/openbb_bridge | OpenBB Platform (AGPL) | Keep AGPL behind HTTP |
| Sentiment | services/sentiment_api | FinRobot agents, Agentic parsers | News/social → sentiment scores |
| Feature Store | packages/qlib_pipelines | Qlib | Canonical factors & training |
| Strategies | src/signals | Qlib primary, FinRL optional | Alpha/signal generation |
| Portfolio & Risk | packages/portfolio_toolkit | Riskfolio, PyPortfolioOpt, Open-Aladdin reports | Optimize weights; risk metrics |
| Backtest/Live | packages/lean_adapter | QuantConnect LEAN | Backtests & live routing |
| UI | apps/dashboard | Atlas patterns (optional) | Visualize pipeline outputs |

## 4. Pipeline Flow (Machine-Readable)
```yaml
pipeline:
  steps:
    - id: fetch_data
      run: services/data_api:fetch
      outputs: [data/prices.parquet, data/fundamentals.parquet, data/macro.parquet, data/news.jsonl]

    - id: feature_store
      run: packages/qlib_pipelines:write_dataset
      inputs: [data/prices.parquet]
      outputs: [features/qlib/**]

    - id: train_factors
      run: packages/qlib_pipelines:train_factor_model
      inputs: [features/qlib/**]
      outputs: [signals/factor.parquet]

    - id: sentiment_scoring
      run: services/sentiment_api:score_news_batch
      inputs: [data/news.jsonl]
      outputs: [sentiment/scores.parquet]

    - id: blend_signals
      run: src/signals:blend
      inputs: [signals/factor.parquet, sentiment/scores.parquet]
      outputs: [signals/final.parquet]

    - id: optimize_portfolio
      run: packages/portfolio_toolkit:optimize
      inputs: [signals/final.parquet]
      outputs: [portfolio/weights.parquet]

    - id: risk_analysis
      run: integrations/open_aladdin:generate_risk_report
      inputs: [data/prices.parquet, portfolio/weights.parquet]
      outputs: [risk/report.json]

    - id: backtest
      run: packages/lean_adapter:backtest
      inputs: [signals/final.parquet, portfolio/weights.parquet]
      outputs: [backtests/equity_curve.csv]

    - id: dashboard
      run: apps/dashboard:start
      inputs: [artifacts/run_*]
```

## 5. Build Plan
```yaml
build_plan:
  - step: core_setup
    tasks: [create_venv, install_requirements, copy_env_example]

  - step: data_layer
    dir: services/data_api
    tasks:
      - implement_endpoints: ["/prices","/fundamentals","/macro","/news"]
      - add_vendor_adapters: ["yfinance","fred","openbb_proxy"]
      - normalize_outputs: ["parquet","jsonl"]

  - step: sentiment_layer
    dir: services/sentiment_api
    tasks:
      - implement_endpoint: "POST /score_news_batch"
      - integrate_agents: ["finrobot"]
      - integrate_parsers: ["agentic_ai_stock_analysis"]
      - output_format: "sentiment/scores.parquet"

  - step: feature_store
    dir: packages/qlib_pipelines
    tasks:
      - write_qlib_dataset
      - train_factor_model
      - export_signals: "signals/factor.parquet"

  - step: strategy_layer
    dir: src/signals
    tasks:
      - implement_blend: {factor_weight: 0.8, sentiment_weight: 0.2}
      - optional_drl: {enabled: false, engine: "finrl"}

  - step: portfolio_and_risk
    dir: packages/portfolio_toolkit
    tasks:
      - optimizer: {engine: "riskfolio", method: "HRP", constraints: {cap_per_name: 0.25}}
      - integrate_open_aladdin_reports: ["var","cvar","stress","factor_exposures"]

  - step: backtest_execution
    dir: packages/lean_adapter
    tasks: [to_lean_alpha, sample_backtest_project]

  - step: engine_enhancements
    dir: .
    tasks:
      - centralize_optimizer: "Use packages.portfolio_toolkit.optimize with blended signal; pipeline calls toolkit"
      - backtest_returns: "Compute equity from historical returns and weights; replace dummy backtest"
      - macro_cache_refresh: "Add refresh=true to /macro to bypass cache; optional TTL"
      - risk_metrics_harden: "Silence FutureWarnings; ensure stable risk stats in report"
      - tests_ci_polish: "Add tests for macro cache, fundamentals key/no-key, optimizer constraints"
      - docs_snippets: "README usage snippets for Data API endpoints and keys"

  - step: dashboard
    dir: apps/dashboard
    tasks:
      - implement_pages: ["Universe","Signals","Sentiment","Portfolio","Risk","Backtests"]
      - data_sources: ["artifacts/run_*"]

  - step: stock_analysis_assistant
    dir: apps/stock_analyzer
    tasks:
      - implement_web_app: "Personal stock analysis with AI recommendations"
      - database_schema: ["metrics_snapshot","factor_scores","recommendations"]
      - scoring_system: "1-5 scale factor scoring with AI explanations"
      - data_providers: ["Alpha Vantage","Finnhub","pandas-ta indicators"]
      - ai_integration: "LLM-powered factor explanations and Buy/Hold/Avoid recommendations"
      - frontend_ui: "Next.js ticker input and analysis display"

  - step: macro_sentiment_geopolitical
    dir: services/macro_sentiment_api
    tasks:
      - macro_data_sources: ["FRED","BEA","BLS","World Bank"]
      - sentiment_sources: ["GDELT","Google News RSS","FinBERT local"]
      - geopolitical_signals: ["GDELT events","government advisories"]
      - etl_workers: ["macro_fred","news_gdelt","rss_ingest","finbert_batch"]
      - database_extensions: ["macro_series","news_articles","sentiment_scores","geo_events"]
      - api_endpoints: ["/macro/snapshot","/sentiment/ticker/{symbol}","/risk/market"]
```

## 6. Config Example
```yaml
config:
  universe: { tickers: ["AAPL","MSFT","NVDA","AMZN","GOOGL","META"] }
  data: { start: "2023-01-01", end: "2025-08-01", vendor_priority: ["openbb","polygon","yfinance"] }
  features: { factors: ["mom_20","vol_20","quality_ttm","value_composite"] }
  sentiment: { enabled: true, sources: ["newsapi","twitter"], agent_framework: "finrobot" }
  signals: { blend_weights: { factor: 0.8, sentiment: 0.2 } }
  portfolio: { optimizer: "riskfolio", method: "HRP", constraints: { cap_per_name: 0.25, sector_caps: {"Tech": 0.5}, turnover_limit: 0.2 } }
  risk: { reports: ["var","cvar","stress","factor_exposures"] }
  backtest: { engine: "lean" }
  outputs: { path: "artifacts/run_{date}" }
```

## 7. CLI
```bash
make setup
make dev
make run-pipeline

docker compose up --build -d
```

## 8. Outputs
| Path | Description |
|---|---|
| data/*.parquet | normalized prices/fundamentals/macro |
| data/news.jsonl | normalized news |
| features/qlib/** | Qlib feature store |
| signals/factor.parquet | factor signals |
| sentiment/scores.parquet | sentiment scores |
| signals/final.parquet | blended signals |
| portfolio/weights.parquet | portfolio weights |
| risk/report.json | risk metrics |
| backtests/equity_curve.csv | LEAN backtest |
| artifacts/run_* | all outputs per run |
