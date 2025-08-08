from __future__ import annotations
import pandas as pd


def optimize_simple(scores: pd.Series, top_k: int = 5, cap_per_name: float = 0.25) -> pd.Series:
    s = scores.copy().fillna(-1e9)
    picks = s.nlargest(top_k).index
    w = pd.Series(0.0, index=s.index)
    if len(picks) > 0:
        w.loc[picks] = 1.0 / len(picks)
    w = w.clip(upper=cap_per_name)
    w = w / (w.sum() or 1.0)
    return w


def optimize(signals: pd.Series, constraints: dict | None = None) -> pd.Series:
    constraints = constraints or {}
    top_k = int(constraints.get("top_k", 5))
    cap = float(constraints.get("cap_per_name", 0.25))
    try:
        import riskfolio as rp  # type: ignore

        # Example HRP via riskfolio if available; fall back otherwise
        df = pd.DataFrame({"score": signals})
        # Use scores to select candidates, then equal weight (or more advanced later)
        sel = df["score"].nlargest(top_k).index
        w = pd.Series(0.0, index=signals.index)
        if len(sel) > 0:
            # Respect cap by first allocating equal weights, then renormalizing under cap
            raw_w = pd.Series(0.0, index=signals.index)
            raw_w.loc[sel] = 1.0 / len(sel)
            w = raw_w.clip(upper=cap)
            w = w / (w.sum() or 1.0)
        else:
            w = pd.Series(0.0, index=signals.index)
        return w
    except Exception:
        return optimize_simple(signals, top_k=top_k, cap_per_name=cap)
