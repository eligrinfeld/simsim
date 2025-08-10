import os
import glob
import json
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Aladdin-ish Dashboard", layout="wide")

# Sidebar navigation
page = st.sidebar.selectbox("Navigate", ["Overview", "Universe", "Signals", "Portfolio", "Risk", "Backtests"])

def _latest_artifacts_dir():
    runs = sorted(glob.glob("artifacts/run_*"))
    return runs[-1] if runs else None

def _load_csv_or_parquet(path_csv: str, path_parq: str):
    if os.path.exists(path_parq):
        return pd.read_parquet(path_parq)
    if os.path.exists(path_csv):
        return pd.read_csv(path_csv)
    return None

def _load_from_artifacts_or_latest(base_csv: str, base_parq: str, artifacts_csv: str = None, artifacts_parq: str = None):
    """Load from top-level first, then artifacts/run_* as fallback."""
    df = _load_csv_or_parquet(base_csv, base_parq)
    if df is None:
        latest = _latest_artifacts_dir()
        if latest:
            ac = artifacts_csv or base_csv.split("/")[-1]
            ap = artifacts_parq or base_parq.split("/")[-1]
            df = _load_csv_or_parquet(os.path.join(latest, ac), os.path.join(latest, ap))
    return df

if page == "Overview":
    st.title("Aladdin-ish Dashboard - Overview")
    col1, col2 = st.columns(2)

    # Portfolio weights
    weights = _load_from_artifacts_or_latest("portfolio/weights.csv", "portfolio/weights.parquet")
    with col1:
        st.subheader("Portfolio Weights")
        if weights is not None:
            if weights.columns[0].lower() in ("ticker", "index"):
                weights = weights.set_index(weights.columns[0])
            st.bar_chart(weights.iloc[:, -1])
        else:
            st.info("No weights found. Run the pipeline to generate portfolio weights.")

    # Signals
    signals = _load_from_artifacts_or_latest("signals/final.csv", "signals/final.parquet")
    with col2:
        st.subheader("Signals (Blended)")
        if signals is not None:
            if signals.columns[0].lower() in ("ticker", "index"):
                signals = signals.set_index(signals.columns[0])
            st.bar_chart(signals.iloc[:, -1])
        else:
            st.info("No signals found.")

    # Risk
    st.subheader("Risk Report")
    latest = _latest_artifacts_dir()
    report_path = None
    if os.path.exists("risk/report.json"):
        report_path = "risk/report.json"
    elif latest and os.path.exists(os.path.join(latest, "risk", "report.json")):
        report_path = os.path.join(latest, "risk", "report.json")

    if report_path:
        with open(report_path) as f:
            rpt = json.load(f)
        st.json(rpt)
    else:
        st.info("No risk report found.")

    # Backtest
    st.subheader("Equity Curve")
    curve = _load_from_artifacts_or_latest("backtests/equity_curve.csv", "backtests/equity_curve.csv")
    if isinstance(curve, pd.DataFrame) and not curve.empty and "equity" in curve.columns:
        curve["date"] = pd.to_datetime(curve["date"], errors="coerce") if "date" in curve.columns else range(len(curve))
        st.line_chart(curve.set_index("date")["equity"])
    else:
        st.info("No equity curve found.")

elif page == "Universe":
    st.title("Universe")
    prices = _load_from_artifacts_or_latest("data/prices.csv", "data/prices.parquet")
    if prices is not None:
        st.subheader("Price Data")
        st.dataframe(prices.head(20))
        if "Ticker" in prices.columns and "Close" in prices.columns:
            st.subheader("Latest Prices by Ticker")
            latest_prices = prices.groupby("Ticker")["Close"].last()
            st.bar_chart(latest_prices)
    else:
        st.info("No price data found.")

elif page == "Signals":
    st.title("Signals")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Factor Signals")
        factor = _load_from_artifacts_or_latest("signals/factor.csv", "signals/factor.parquet")
        if factor is not None:
            if factor.columns[0].lower() in ("ticker", "index"):
                factor = factor.set_index(factor.columns[0])
            st.bar_chart(factor.iloc[:, -1])
            st.dataframe(factor)
        else:
            st.info("No factor signals found.")

    with col2:
        st.subheader("Final (Blended) Signals")
        final = _load_from_artifacts_or_latest("signals/final.csv", "signals/final.parquet")
        if final is not None:
            if final.columns[0].lower() in ("ticker", "index"):
                final = final.set_index(final.columns[0])
            st.bar_chart(final.iloc[:, -1])
            st.dataframe(final)
        else:
            st.info("No final signals found.")

elif page == "Portfolio":
    st.title("Portfolio")
    weights = _load_from_artifacts_or_latest("portfolio/weights.csv", "portfolio/weights.parquet")
    if weights is not None:
        st.subheader("Portfolio Weights")
        if weights.columns[0].lower() in ("ticker", "index"):
            weights = weights.set_index(weights.columns[0])
        st.bar_chart(weights.iloc[:, -1])
        st.dataframe(weights)

        # Portfolio stats
        w = weights.iloc[:, -1]
        st.subheader("Portfolio Statistics")
        st.metric("Number of Holdings", (w > 0).sum())
        st.metric("Max Weight", f"{w.max():.1%}")
        st.metric("Weight Sum", f"{w.sum():.1%}")
    else:
        st.info("No portfolio weights found.")

elif page == "Risk":
    st.title("Risk Analysis")
    latest = _latest_artifacts_dir()
    report_path = None
    if os.path.exists("risk/report.json"):
        report_path = "risk/report.json"
    elif latest and os.path.exists(os.path.join(latest, "risk", "report.json")):
        report_path = os.path.join(latest, "risk", "report.json")

    if report_path:
        with open(report_path) as f:
            rpt = json.load(f)

        st.subheader("Risk Metrics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Annual Volatility", f"{rpt.get('vol_annual', 0):.1%}")
        with col2:
            st.metric("Max Drawdown", f"{rpt.get('max_drawdown', 0):.1%}")
        with col3:
            st.metric("VaR (5%)", f"{rpt.get('VaR_5pct', 0):.1%}")
        with col4:
            st.metric("CVaR (5%)", f"{rpt.get('CVaR_5pct', 0):.1%}")

        st.subheader("Full Risk Report")
        st.json(rpt)
    else:
        st.info("No risk report found.")

elif page == "Backtests":
    st.title("Backtests")
    curve = _load_from_artifacts_or_latest("backtests/equity_curve.csv", "backtests/equity_curve.csv")
    if isinstance(curve, pd.DataFrame) and not curve.empty and "equity" in curve.columns:
        st.subheader("Equity Curve")
        curve["date"] = pd.to_datetime(curve["date"], errors="coerce") if "date" in curve.columns else range(len(curve))
        st.line_chart(curve.set_index("date")["equity"])

        st.subheader("Performance Statistics")
        equity = curve["equity"]
        total_return = (equity.iloc[-1] / equity.iloc[0] - 1) if len(equity) > 1 else 0
        st.metric("Total Return", f"{total_return:.1%}")

        st.subheader("Equity Data")
        st.dataframe(curve)
    else:
        st.info("No equity curve found.")
