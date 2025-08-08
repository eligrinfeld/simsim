import os
import glob
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Aladdin-ish Dashboard", layout="wide")
st.title("Aladdin-ish Dashboard")


def _latest_artifacts_dir():
    runs = sorted(glob.glob("artifacts/run_*"))
    return runs[-1] if runs else None


def _load_csv_or_parquet(path_csv: str, path_parq: str):
    if os.path.exists(path_parq):
        return pd.read_parquet(path_parq)
    if os.path.exists(path_csv):
        return pd.read_csv(path_csv)
    return None


col1, col2 = st.columns(2)

# Portfolio weights
weights = _load_csv_or_parquet("portfolio/weights.csv", "portfolio/weights.parquet")
if weights is None:
    latest = _latest_artifacts_dir()
    if latest:
        weights = _load_csv_or_parquet(os.path.join(latest, "weights.csv"), os.path.join(latest, "weights.parquet"))

with col1:
    st.subheader("Portfolio Weights")
    if weights is not None:
        # If index column present
        if weights.columns[0].lower() in ("ticker", "index"):
            weights = weights.set_index(weights.columns[0])
        st.bar_chart(weights.iloc[:, -1])
    else:
        st.info("No weights found. Run the pipeline to generate portfolio weights.")

# Signals
signals = _load_csv_or_parquet("signals/final.csv", "signals/final.parquet")
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
    import json

    with open(report_path) as f:
        rpt = json.load(f)
    st.json(rpt)
else:
    st.info("No risk report found.")

# Backtest
st.subheader("Equity Curve")
curve = _load_csv_or_parquet("backtests/equity_curve.csv", os.path.join(_latest_artifacts_dir() or "", "backtests", "equity_curve.csv"))
if isinstance(curve, pd.DataFrame) and not curve.empty and "equity" in curve.columns:
    curve["date"] = pd.to_datetime(curve["date"]) if "date" in curve.columns else range(len(curve))
    st.line_chart(curve.set_index("date")["equity"])
else:
    st.info("No equity curve found.")
