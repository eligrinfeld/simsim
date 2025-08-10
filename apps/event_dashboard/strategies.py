from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

# Candles are dicts: {time, open, high, low, close, volume}


def sma(vals: List[float], n: int) -> List[float]:
    out: List[float] = []
    s = 0.0
    for i, v in enumerate(vals):
        s += v
        if i >= n:
            s -= vals[i - n]
        if i >= n - 1:
            out.append(s / n)
        else:
            out.append(float('nan'))
    return out


def stdev(vals: List[float], n: int) -> List[float]:
    out: List[float] = []
    s = 0.0
    s2 = 0.0
    for i, v in enumerate(vals):
        s += v
        s2 += v * v
        if i >= n:
            s -= vals[i - n]
            s2 -= vals[i - n] * vals[i - n]
        if i >= n - 1:
            mean = s / n
            var = max(0.0, s2 / n - mean * mean)
            out.append(math.sqrt(var))
        else:
            out.append(float('nan'))
    return out


def rsi(vals: List[float], n: int = 14) -> List[float]:
    gains = [0.0]
    losses = [0.0]
    for i in range(1, len(vals)):
        ch = vals[i] - vals[i - 1]
        gains.append(max(0.0, ch))
        losses.append(max(0.0, -ch))
    out = [float('nan')] * len(vals)
    if len(vals) < n + 1:
        return out
    avg_gain = sum(gains[1 : n + 1]) / n
    avg_loss = sum(losses[1 : n + 1]) / n
    out[n] = 100.0 - 100.0 / (1.0 + (avg_gain / (avg_loss or 1e-9)))
    for i in range(n + 1, len(vals)):
        avg_gain = (avg_gain * (n - 1) + gains[i]) / n
        avg_loss = (avg_loss * (n - 1) + losses[i]) / n
        out[i] = 100.0 - 100.0 / (1.0 + (avg_gain / (avg_loss or 1e-9)))
    return out


@dataclass
class BacktestResult:
    name: str
    total_return: float
    sharpe: float
    max_drawdown: float
    trades: List[Dict[str, Any]]  # {ts, side, price}
    details: Dict[str, Any]


def evaluate_position_returns(closes: List[float], position: List[int]) -> Tuple[List[float], float, float]:
    # per-step returns using close-to-close when in position
    rets: List[float] = [0.0]
    eq = 1.0
    peak = 1.0
    max_dd = 0.0
    for i in range(1, len(closes)):
        r = (closes[i] / closes[i - 1] - 1.0) * (1 if position[i - 1] else 0)
        rets.append(r)
        eq *= (1.0 + r)
        peak = max(peak, eq)
        max_dd = min(max_dd, eq / peak - 1.0)
    return rets, eq - 1.0, max_dd


def sharpe_ratio(rets: List[float]) -> float:
    if not rets:
        return 0.0
    m = sum(rets) / len(rets)
    v = sum((x - m) ** 2 for x in rets) / (len(rets) or 1)
    sd = math.sqrt(max(1e-12, v))
    return m / sd if sd > 0 else 0.0


def moving_avg_cross(candles: List[Dict[str, Any]], short=10, long=20) -> BacktestResult:
    closes = [c["close"] for c in candles]
    ma_s = sma(closes, short)
    ma_l = sma(closes, long)
    pos = [1 if (not math.isnan(ma_s[i]) and not math.isnan(ma_l[i]) and ma_s[i] > ma_l[i]) else 0 for i in range(len(closes))]
    rets, total, mdd = evaluate_position_returns(closes, pos)
    sh = sharpe_ratio(rets)
    # Trades as crossovers
    trades: List[Dict[str, Any]] = []
    cur = 0
    for i in range(1, len(pos)):
        if pos[i] != cur:
            cur = pos[i]
            side = "buy" if cur == 1 else "sell"
            trades.append({"ts": candles[i]["time"], "side": side, "price": closes[i]})
    return BacktestResult(
        name=f"MovingAvgCross({short},{long})", total_return=total, sharpe=sh, max_drawdown=mdd, trades=trades,
        details={"short": short, "long": long}
    )


def bollinger_breakout(candles: List[Dict[str, Any]], period=20, k=2.0) -> BacktestResult:
    closes = [c["close"] for c in candles]
    mid = sma(closes, period)
    sd = stdev(closes, period)
    upper = [mid[i] + k * sd[i] if not math.isnan(mid[i]) else float('nan') for i in range(len(closes))]
    pos = [1 if (not math.isnan(upper[i]) and closes[i] > upper[i]) else 0 for i in range(len(closes))]
    rets, total, mdd = evaluate_position_returns(closes, pos)
    sh = sharpe_ratio(rets)
    trades: List[Dict[str, Any]] = []
    cur = 0
    for i in range(1, len(pos)):
        if pos[i] != cur:
            cur = pos[i]
            side = "buy" if cur == 1 else "sell"
            trades.append({"ts": candles[i]["time"], "side": side, "price": closes[i]})
    return BacktestResult(
        name=f"BollingerBreakout({period},{k})", total_return=total, sharpe=sh, max_drawdown=mdd, trades=trades,
        details={"period": period, "k": k}
    )


def rsi_reversion(candles: List[Dict[str, Any]], period=14, buy_th=30.0, exit_th=55.0) -> BacktestResult:
    closes = [c["close"] for c in candles]
    r = rsi(closes, period)
    pos = [0] * len(closes)
    holding = False
    for i in range(len(closes)):
        if not holding and (not math.isnan(r[i]) and r[i] <= buy_th):
            holding = True
        elif holding and (not math.isnan(r[i]) and r[i] >= exit_th):
            holding = False
        pos[i] = 1 if holding else 0
    rets, total, mdd = evaluate_position_returns(closes, pos)
    sh = sharpe_ratio(rets)
    trades: List[Dict[str, Any]] = []
    cur = 0
    for i in range(1, len(pos)):
        if pos[i] != cur:
            cur = pos[i]
            side = "buy" if cur == 1 else "sell"
            trades.append({"ts": candles[i]["time"], "side": side, "price": closes[i]})
    return BacktestResult(
        name=f"RSI({period},{buy_th},{exit_th})", total_return=total, sharpe=sh, max_drawdown=mdd, trades=trades,
        details={"period": period, "buy": buy_th, "exit": exit_th}
    )


def pick_best(candles: List[Dict[str, Any]]) -> BacktestResult:
    """Evaluate a small library of strategies and pick by Sharpe, then Total Return."""
    if len(candles) < 30:
        # Not enough data: return a no-op result
        return BacktestResult("NoStrategy", 0.0, 0.0, 0.0, [], {})

    cands = [
        moving_avg_cross(candles, 10, 20),
        moving_avg_cross(candles, 20, 50),
        bollinger_breakout(candles, 20, 2.0),
        rsi_reversion(candles, 14, 30.0, 55.0),
    ]
    cands.sort(key=lambda x: (x.sharpe, x.total_return))
    best = cands[-1]
    return best


def explain(best: BacktestResult) -> str:
    name = best.name
    tr = best.total_return
    sh = best.sharpe
    mdd = best.max_drawdown
    ntrades = sum(1 for t in best.trades if t["side"] == "buy")
    para1 = (
        f"The optimal strategy is {name}. It achieved a total return of {tr:.2%} with a Sharpe of {sh:.2f} "
        f"and a maximum drawdown of {mdd:.2%}. This balance of returns versus risk outperformed the other candidates."
    )
    para2 = (
        f"Across {ntrades} entries, the strategy captured the prevailing structure in the recent data (trend/mean-reversion), "
        f"while keeping drawdowns contained. Its rules fit the current volatility regime better than alternatives, leading to a superior risk-adjusted profile."
    )
    return para1 + "\n\n" + para2

