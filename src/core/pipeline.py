import argparse
import os
import yaml

from src.data.loader import load_timeseries
from src.signals.alpha import compute_signals
from src.signals.blend import blend
from src.sentiment.news import score_sentiment
from src.core.report import make_report
from src.core.utils import (
    ensure_dir,
    resolve_artifacts_path,
    write_parquet_or_csv,
    write_series_parquet_or_csv,
)
from packages.qlib_pipelines import write_qlib_dataset
from packages.lean_adapter import backtest as run_backtest
from packages.portfolio_toolkit import optimize as tk_optimize


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config))

    tickers = cfg["universe"]["tickers"]
    start = cfg["data"]["start"]
    end = cfg["data"]["end"]

    outputs_cfg = cfg.get("outputs", {"path": "artifacts/run_{date}"})
    run_dir = resolve_artifacts_path(outputs_cfg)
    ensure_dir(run_dir)

    # 1) Load data and persist
    df = load_timeseries(tickers, start, end)
    ensure_dir("data")
    write_parquet_or_csv(df.reset_index(), "data/prices.parquet")
    # Mirror under artifacts
    write_parquet_or_csv(df.reset_index(), os.path.join(run_dir, "prices.parquet"))

    # 2) Compute factor signals and persist
    sigs = compute_signals(df, cfg.get("features", {}))
    factor_series = next(iter(sigs.values())) if sigs else None
    ensure_dir("signals")
    if factor_series is not None:
        write_series_parquet_or_csv(
            factor_series, "signals/factor.parquet", name="score"
        )
        write_series_parquet_or_csv(
            factor_series, os.path.join(run_dir, "factor.parquet"), name="score"
        )
        # Write minimal qlib dataset stub per PRD
        write_qlib_dataset(df)

    # 3) Optional sentiment
    sent_series = None
    if cfg.get("sentiment", {}).get("enabled", False):
        s = score_sentiment(tickers, start, end, cfg["sentiment"]) or {}
        if isinstance(s, dict) and "score" in s and s["score"] is not None:
            sent_series = s["score"]

    # 4) Blend signals per config
    bw = cfg.get("signals", {}).get("blend_weights", {"factor": 0.8, "sentiment": 0.2})
    blended = blend(sigs, sent_series, bw)
    write_series_parquet_or_csv(blended, "signals/final.parquet", name="score")
    write_series_parquet_or_csv(
        blended, os.path.join(run_dir, "final.parquet"), name="score"
    )

    # 5) Optimize portfolio (centralized in toolkit) and persist
    constraints = cfg.get("portfolio", {}).get("constraints", {})
    weights = tk_optimize(blended, constraints=constraints)
    ensure_dir("portfolio")
    try:
        write_series_parquet_or_csv(weights, "portfolio/weights.parquet", name="weight")
        write_series_parquet_or_csv(
            weights, os.path.join(run_dir, "weights.parquet"), name="weight"
        )
    except Exception:
        pass

    # 6) Backtest stub and persist
    ensure_dir("backtests")
    equity_path = run_backtest(
        os.path.join(run_dir, "final.parquet"),
        os.path.join(run_dir, "weights.parquet"),
        outdir="backtests",
    )
    # Mirror to artifacts
    ensure_dir(os.path.join(run_dir, "backtests"))
    try:
        import shutil

        shutil.copy2(
            equity_path,
            os.path.join(run_dir, "backtests", os.path.basename(equity_path)),
        )
    except Exception:
        pass

    # Risk report under both artifacts and top-level risk/
    ensure_dir("risk")
    print(
        make_report(
            df, sigs, sent_series, weights, outdir=os.path.join(run_dir, "risk")
        )
    )
    print(make_report(df, sigs, sent_series, weights, outdir="risk"))


if __name__ == "__main__":
    main()
