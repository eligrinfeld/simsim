from __future__ import annotations
import os
import pandas as pd


def to_lean_dataset(df: pd.DataFrame):
    return df


def backtest_from_prices_and_weights(px: pd.DataFrame, weights: pd.Series) -> pd.DataFrame:
    """
    Compute a simple returns-based equity curve:
    - px: wide DataFrame of prices indexed by Date with ticker columns
    - weights: Series of final weights indexed by ticker (sum to 1)
    Rebalance once at the start and hold weights constant.
    """
    # Ensure datetime index and numeric prices
    px = px.copy()
    px.index = pd.to_datetime(px.index, errors="coerce")
    px = px.sort_index()
    px = px.apply(pd.to_numeric, errors="coerce")

    rets = px.pct_change(fill_method=None).fillna(0.0)
    # Align columns to weights index
    aligned = rets.reindex(columns=weights.index).fillna(0.0)
    # Ensure numeric weights
    weights = pd.to_numeric(weights, errors="coerce").fillna(0.0)
    port_ret = (aligned * weights).sum(axis=1)
    equity = (1.0 + port_ret).cumprod()
    return pd.DataFrame({"date": equity.index, "equity": equity.values})


def backtest(signals_path: str, weights_path: str, outdir: str = "backtests") -> str:
    """
    Compatibility entrypoint: load prices from artifacts if present and compute equity.
    As a minimal approach, this function looks for data/prices.(parquet|csv) and
    portfolio/weights.(parquet|csv) and computes a single-period rebalanced equity curve.
    """
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "equity_curve.csv")

    # Load weights
    w = None
    for wp in ("portfolio/weights.parquet", "portfolio/weights.csv"):
        if os.path.exists(wp):
            if wp.endswith(".parquet"):
                wdf = pd.read_parquet(wp)
            else:
                wdf = pd.read_csv(wp)
            name = wdf.columns[-1]
            w = wdf.set_index(wdf.columns[0])[name]
            break

    # Load prices
    px = None
    for dp in ("data/prices.parquet", "data/prices.csv"):
        if os.path.exists(dp):
            if dp.endswith(".parquet"):
                df = pd.read_parquet(dp)
            else:
                df = pd.read_csv(dp)
            # Expect columns: Date, Ticker, ... Close
            if {"Date", "Ticker", "Close"}.issubset(df.columns):
                px = df.pivot(index="Date", columns="Ticker", values="Close")
            else:
                # If already wide
                df = df.copy()
                dt_col = df.columns[0]
                df = df.set_index(dt_col)
                px = df
            break

    if px is None or w is None or w.sum() == 0:
        # Write a minimal placeholder if data missing
        pd.DataFrame({"date": pd.date_range("2024-01-01", periods=2, freq="B"), "equity": [1.0, 1.0]}).to_csv(path, index=False)
        return path

    curve = backtest_from_prices_and_weights(px, w)
    curve.to_csv(path, index=False)
    return path
