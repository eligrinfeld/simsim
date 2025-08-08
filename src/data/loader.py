import pandas as pd
import yfinance as yf


def load_timeseries(tickers, start, end):
    # Build a list of per-ticker DataFrames to avoid name collisions when resetting index
    frames = []
    for t in tickers:
        df = yf.download(t, start=start, end=end, progress=False, auto_adjust=True)
        df["Ticker"] = t
        frames.append(df)

    # Concatenate and create a MultiIndex on (Date, Ticker)
    out = pd.concat(frames)
    out = out.reset_index(names="Date").set_index(["Date", "Ticker"]).sort_index()
    return out
