from __future__ import annotations
import pandas as pd
from typing import Dict, Optional


def blend(
    factors: Dict[str, pd.Series],
    sentiment: Optional[pd.Series],
    weights: Dict[str, float],
) -> pd.Series:
    """
    Blend factor signals and optional sentiment signal into a single score per ticker.

    - factors: dict of named factor series indexed by ticker (e.g., {"mom_20": Series, ...})
    - sentiment: optional Series indexed by ticker (already aligned), or None
    - weights: {factor: float, sentiment: float}

    Returns: Series of blended scores indexed by ticker.
    """
    fw = float(weights.get("factor", 1.0))
    sw = float(weights.get("sentiment", 0.0))

    # Simple factor composite: if multiple factors present, average their z-scores; else use the first
    comp: Optional[pd.Series] = None
    if factors:
        # Normalize each factor (z-score) to reduce scale issues, then average
        zed = []
        for s in factors.values():
            s = s.astype("float64")
            if s.std(ddof=0) and s.std(ddof=0) > 0:
                z = (s - s.mean()) / (s.std(ddof=0) or 1.0)
            else:
                z = s * 0.0
            zed.append(z)
        comp = pd.concat(zed, axis=1).mean(axis=1)
    else:
        comp = None

    # Align and blend
    if comp is None and sentiment is None:
        return pd.Series(dtype="float64")

    if comp is None:
        comp = pd.Series(0.0, index=sentiment.index)
    if sentiment is None:
        sentiment = pd.Series(0.0, index=comp.index)

    comp, sentiment = comp.align(sentiment, join="outer", fill_value=0.0)
    final = fw * comp + sw * sentiment
    return final.fillna(0.0)
