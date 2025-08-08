from __future__ import annotations
import json
import os
import pandas as pd


def _compute_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = (equity / peak - 1.0).min()
    return float(dd)


def make_report(df, sigs, sent, weights, outdir: str | None = None):
    lines = [
        "=== Pipeline Report ===",
        f"Weights:\n{weights.round(4).to_string()}",
        "\nSignals:",
    ]
    for k, v in sigs.items():
        lines.append(f"- {k}: sample\n{v.round(4).to_string()}")

    text = "\n".join(lines)

    # Optionally write a basic risk report JSON using daily returns
    if outdir:
        os.makedirs(outdir, exist_ok=True)
        try:
            px = df["Close"].unstack("Ticker")
            rets = px.pct_change(fill_method=None).dropna(how="all")
            # Portfolio equity (naive): sum(weights * (1+ret)).cumprod()
            aligned = rets.reindex(columns=weights.index).fillna(0.0)
            port_ret = (aligned * weights).sum(axis=1)
            equity = (1.0 + port_ret).cumprod()
            vol = float(port_ret.std() * (252 ** 0.5)) if len(port_ret) else 0.0
            mdd = _compute_drawdown(equity) if len(equity) else 0.0
            var = float(port_ret.quantile(0.05)) if len(port_ret) else 0.0
            cvar = float(port_ret[port_ret <= var].mean()) if len(port_ret) else 0.0

            report = {
                "universe_size": int(weights.size),
                "nonzero": int((weights > 0).sum()),
                "weight_sum": float(weights.sum()),
                "max_weight": float(weights.max()) if weights.size else 0.0,
                "vol_annual": vol,
                "max_drawdown": mdd,
                "VaR_5pct": var,
                "CVaR_5pct": cvar,
            }
            with open(os.path.join(outdir, "report.json"), "w") as f:
                json.dump(report, f, indent=2)
        except Exception:
            pass
    return text
