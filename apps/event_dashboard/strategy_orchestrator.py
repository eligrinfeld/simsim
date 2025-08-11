from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# Local strategy primitives
import strategies as st
from pine_adapter import compile_pine


@dataclass
class RankedResult:
    name: str
    total_return: float
    sharpe: float
    max_drawdown: float
    trades: List[Dict[str, Any]]
    details: Dict[str, Any]

    @property
    def trade_count(self) -> int:
        return sum(1 for t in self.trades if t.get("side") == "buy")


def _grid_moving_avg() -> List[Tuple[int, int]]:
    shorts = [5, 10, 20]
    longs = [20, 50, 100]
    out: List[Tuple[int, int]] = []
    for s in shorts:
        for l in longs:
            if s < l:
                out.append((s, l))
    return out


def _grid_bbands() -> List[Tuple[int, float]]:
    periods = [20, 40]
    ks = [1.5, 2.0, 2.5]
    return [(p, k) for p in periods for k in ks]


def _grid_rsi_reversion() -> List[Tuple[int, float, float]]:
    # (period, buy_th, exit_th)
    buys = [25.0, 30.0, 35.0]
    exits = [50.0, 55.0, 60.0]
    return [(14, b, e) for b in buys for e in exits if b < e]


def _accept(result: RankedResult, min_trades: int, max_dd: float) -> bool:
    if result.trade_count < min_trades:
        return False
    if result.max_drawdown < max_dd:
        return False
    if math.isnan(result.sharpe) or math.isnan(result.total_return):
        return False
    return True


def evaluate_grid(
    candles: List[Dict[str, Any]],
    pine_codes: Optional[List[str]] = None,
    *,
    min_trades: int = 3,
    max_drawdown: float = -0.25,
) -> List[RankedResult]:
    """
    Evaluate a parameter grid of built-in strategies and optional Pine programs
    on the provided candles, and return ranked results.

    Ranking: by Sharpe (desc), tiebreaker by total return (desc).
    Filters: min_trades, drawdown >= max_drawdown.
    """
    if not candles or len(candles) < 50:
        return []

    results: List[RankedResult] = []

    # Built-ins
    for s, l in _grid_moving_avg():
        res = st.moving_avg_cross(candles, short=s, long=l)
        results.append(RankedResult(res.name, res.total_return, res.sharpe, res.max_drawdown, res.trades, res.details))

    for p, k in _grid_bbands():
        res = st.bollinger_breakout(candles, period=p, k=k)
        results.append(RankedResult(res.name, res.total_return, res.sharpe, res.max_drawdown, res.trades, res.details))

    for per, b, e in _grid_rsi_reversion():
        res = st.rsi_reversion(candles, period=per, buy_th=b, exit_th=e)
        results.append(RankedResult(res.name, res.total_return, res.sharpe, res.max_drawdown, res.trades, res.details))

    # Pine strategies (optional)
    for code in (pine_codes or []):
        try:
            comp = compile_pine(code)
            res = comp.run(candles)
            results.append(RankedResult(res.name, res.total_return, res.sharpe, res.max_drawdown, res.trades, res.details))
        except Exception:
            # Ignore bad pine for now
            continue

    # Filter
    filtered = [r for r in results if _accept(r, min_trades=min_trades, max_dd=max_drawdown)]
    if not filtered:
        # fallback: keep best Sharpe regardless of filters
        filtered = results

    # Rank
    filtered.sort(key=lambda r: (r.sharpe, r.total_return))
    filtered = list(reversed(filtered))
    return filtered


__all__ = ["evaluate_grid", "RankedResult"]

