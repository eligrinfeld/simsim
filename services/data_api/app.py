from __future__ import annotations
from fastapi import FastAPI, HTTPException
from typing import Optional
import os
import re
import requests

app = FastAPI(title="Data API Gateway")


def _get_env_var(name: str) -> Optional[str]:
    """Get env var from process or .env file (fallback) without requiring python-dotenv."""
    val = os.getenv(name)
    if val:
        return val
    try:
        for path in (".env", "../.env"):
            if os.path.exists(path):
                with open(path) as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if line.startswith(name + "="):
                            return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return None


def _get_sec_api_key() -> Optional[str]:
    return _get_env_var("SEC_API_KEY")


def _get_fred_api_key() -> Optional[str]:
    return _get_env_var("FRED_API_KEY")


def _macro_cache_dir() -> str:
    d = os.path.join("data", "macro")
    os.makedirs(d, exist_ok=True)
    return d


def _macro_cache_path(series_id: str, observation_start: Optional[str], observation_end: Optional[str]) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", series_id)
    s = observation_start or ""
    e = observation_end or ""
    key = f"{safe}__{s}__{e}".strip("_") or safe
    return os.path.join(_macro_cache_dir(), key + ".json")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/prices")
def prices(
    ticker: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    interval: Optional[str] = None,
):
    """
    Return normalized OHLCV price data for a ticker using yfinance.
    Dates are ISO strings (YYYY-MM-DD). Interval optional (e.g., 1d, 1wk, 1mo).
    """
    try:
        kwargs = {"progress": False, "auto_adjust": True}
        if start:
            kwargs["start"] = start
        if end:
            kwargs["end"] = end
        if interval:
            kwargs["interval"] = interval
        import yfinance as yf  # local import so tests don't require it at import time
        df = yf.download(ticker, **kwargs)
        if df is None or df.empty:
            return {"ticker": ticker, "start": start, "end": end, "prices": []}
        df = df.reset_index().rename(
            columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
            }
        )
        records = df[["date", "open", "high", "low", "close", "volume"]].to_dict(
            orient="records"
        )
        return {"ticker": ticker, "start": start, "end": end, "prices": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/macro")
def macro(
    series_id: str,
    observation_start: Optional[str] = None,
    observation_end: Optional[str] = None,
    refresh: Optional[bool] = False,
    ttl_seconds: Optional[int] = 86400,
):
    """
    Fetch a FRED series by ID using the official FRED API.
    Docs: https://fred.stlouisfed.org/docs/api/fred/series_observations.html

    - series_id: e.g., CPIAUCSL, UNRATE, DGS10
    - observation_start, observation_end: optional YYYY-MM-DD
    - refresh: if true, bypass cache and refresh from FRED
    - ttl_seconds: cache time-to-live; if expired, fetch fresh
    """
    url = "https://api.stlouisfed.org/fred/series/observations"
    path = _macro_cache_path(series_id, observation_start, observation_end)

    # Try cache first unless refresh is requested
    try:
        use_cache = os.path.exists(path) and not refresh
        if use_cache and ttl_seconds is not None:
            try:
                import time

                age = time.time() - os.path.getmtime(path)
                if age > ttl_seconds:
                    use_cache = False
            except Exception:
                use_cache = False

        if use_cache:
            with open(path) as f:
                cached = f.read()
            try:
                import json as _json

                data = _json.loads(cached)
            except Exception:
                data = None
            if isinstance(data, dict) and "observations" in data:
                obs = data.get("observations", [])
                out = []
                for o in obs:
                    val = o.get("value")
                    try:
                        v = float(val)
                    except Exception:
                        v = None
                    out.append({"date": o.get("date"), "value": v})
                return {"series_id": series_id, "values": out}
    except Exception:
        # Ignore cache errors and fall back to network
        pass

    # No usable cache; fetch from FRED if key is available
    api_key = _get_fred_api_key()
    if not api_key:
        # Graceful fallback if key not set and no cache available
        return {"series_id": series_id, "values": []}

    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
    }
    if observation_start:
        params["observation_start"] = observation_start
    if observation_end:
        params["observation_end"] = observation_end

    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        # Write cache
        try:
            with open(path, "w") as f:
                f.write(r.text)
        except Exception:
            pass
        obs = data.get("observations", [])
        # Normalize to (date, value) float where possible (FRED returns values as strings)
        out = []
        for o in obs:
            val = o.get("value")
            try:
                v = float(val)
            except Exception:
                v = None
            out.append({"date": o.get("date"), "value": v})
        return {"series_id": series_id, "values": out}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FRED error: {e}")


@app.get("/fundamentals")
def fundamentals(ticker: str):
    """
    Fundamentals via SEC API (optional): If SEC_API_KEY is set and sec_api is installed,
    fetch recent 10-K/10-Q filing metadata. Falls back to empty object if unavailable.
    """
    api_key = _get_sec_api_key()
    if not api_key:
        return {"ticker": ticker, "fundamentals": {}}

    try:
        from sec_api import QueryApi  # type: ignore

        query_api = QueryApi(api_key=api_key)
        query = {
            "query": {"query_string": {"query": f"ticker:{ticker} AND formType:(10-K OR 10-Q)"}},
            "from": "0",
            "size": "5",
            "sort": [{"filedAt": {"order": "desc"}}],
        }
        res = query_api.get_filings(query)
        filings = [
            {
                "formType": f.get("formType"),
                "filedAt": f.get("filedAt"),
                "companyName": f.get("companyName"),
                "cik": f.get("cik"),
                "linkToFilingDetails": f.get("linkToFilingDetails"),
            }
            for f in res.get("filings", [])
        ]
        return {"ticker": ticker, "fundamentals": {"sec_filings": filings}}
    except Exception:
        # If sec_api not installed or any error occurs, return empty fundamentals
        return {"ticker": ticker, "fundamentals": {}}


@app.get("/news")
def news(query: Optional[str] = None):
    """
    Placeholder news search endpoint. Returns an empty list by default.
    Later can integrate a provider and support pagination.
    """
    return {"query": query, "articles": []}
