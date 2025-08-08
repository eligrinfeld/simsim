from __future__ import annotations
import pandas as pd


def score_sentiment(tickers, start, end, cfg):
    # Placeholder: neutral sentiment (zeros) per ticker
    idx = pd.Index(tickers, name="Ticker")
    series = pd.Series(0.0, index=idx, name="sentiment")
    return {"score": series}
