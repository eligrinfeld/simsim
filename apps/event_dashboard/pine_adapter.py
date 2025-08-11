from __future__ import annotations
import re
import math
from dataclasses import dataclass
from typing import Any, Dict, List

import strategies as st

# Pine subset translator (extended MVP)
# Supported:
# - input.int / input.float assignments
# - Indicators: ta.sma, ta.ema, ta.rsi, ta.bbands, ta.macd, ta.stoch, ta.supertrend
#   (bbands/macd/stoch/supertrend use tuple assignment on LHS)
# - Cross conditions: ta.crossover(a,b), ta.crossunder(a,b)
# - Threshold conditions: if series <num|<=|>=|> number: strategy.entry/close
# - Entries/exits: strategy.entry('Long'...), strategy.close('Long')
# Limits: single symbol, long-only, one position at a time, no pyramiding, minimal expr grammar


@dataclass
class CompiledStrategy:
    name: str
    params: Dict[str, Any]
    # Program in a tiny IR
    series: Dict[str, Any]
    # cond types: ('crossover','a','b') | ('crossunder','a','b') | ('cmp','series','<',value)
    rules: List[Dict[str, Any]]

    def run(self, candles: List[Dict[str, Any]]):
        closes = [c["close"] for c in candles]
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        opens = [c["open"] for c in candles]

        series_cache: Dict[str, List[float]] = {
            "close": closes,
            "high": highs,
            "low": lows,
            "open": opens,
        }

        def ema(vals: List[float], n: int) -> List[float]:
            if not vals:
                return []
            k = 2 / (n + 1)
            out: List[float] = []
            prev = vals[0]
            for v in vals:
                prev = v * k + prev * (1 - k)
                out.append(prev)
            return out

        def atr(h: List[float], l: List[float], c: List[float], n: int) -> List[float]:
            tr: List[float] = []
            prev_c = c[0] if c else 0.0
            for i in range(len(c)):
                hi, lo, cl = h[i], l[i], c[i]
                tr_val = max(hi - lo, abs(hi - prev_c), abs(lo - prev_c))
                tr.append(tr_val)
                prev_c = cl
            # Wilder's smoothing approx via EMA
            return ema(tr, max(1, n))

        # Helper to resolve parameter values
        def resolve_param(val_str: str) -> float:
            try:
                return float(val_str)
            except ValueError:
                # Try to resolve as a parameter name
                return float(self.params.get(val_str, val_str))

        # materialize indicators
        for name, spec in self.series.items():
            kind = spec[0]
            if kind == "sma":
                src, n = spec[1], resolve_param(spec[2])
                series_cache[name] = st.sma(series_cache[src], int(n))
            elif kind == "ema":
                src, n = spec[1], resolve_param(spec[2])
                series_cache[name] = ema(series_cache[src], int(n))
            elif kind == "rsi":
                src, n = spec[1], resolve_param(spec[2])
                series_cache[name] = st.rsi(series_cache[src], int(n))
            elif kind == "bb_basis":
                src, n, k = spec[1], resolve_param(spec[2]), resolve_param(spec[3])
                mid = st.sma(series_cache[src], int(n))
                sd = st.stdev(series_cache[src], int(n))
                series_cache[name] = mid
                # Upper/Lower will be computed in their own entries
            elif kind == "bb_upper":
                src, n, k = spec[1], resolve_param(spec[2]), resolve_param(spec[3])
                mid = st.sma(series_cache[src], int(n))
                sd = st.stdev(series_cache[src], int(n))
                series_cache[name] = [mid[i] + k * sd[i] if not math.isnan(mid[i]) else math.nan for i in range(len(mid))]
            elif kind == "bb_lower":
                src, n, k = spec[1], resolve_param(spec[2]), resolve_param(spec[3])
                mid = st.sma(series_cache[src], int(n))
                sd = st.stdev(series_cache[src], int(n))
                series_cache[name] = [mid[i] - k * sd[i] if not math.isnan(mid[i]) else math.nan for i in range(len(mid))]
            elif kind == "macd":
                src, f, s, sig = spec[1], resolve_param(spec[2]), resolve_param(spec[3]), resolve_param(spec[4])
                efast = ema(series_cache[src], int(f))
                eslow = ema(series_cache[src], int(s))
                macd_line = [efast[i] - eslow[i] for i in range(len(efast))]
                series_cache[name] = macd_line
            elif kind == "macd_signal":
                src, f, s, sig = spec[1], int(spec[2]), int(spec[3]), int(spec[4])
                efast = ema(series_cache[src], f)
                eslow = ema(series_cache[src], s)
                macd_line = [efast[i] - eslow[i] for i in range(len(efast))]
                series_cache[name] = ema(macd_line, sig)
            elif kind == "macd_hist":
                src, f, s, sig = spec[1], int(spec[2]), int(spec[3]), int(spec[4])
                efast = ema(series_cache[src], f)
                eslow = ema(series_cache[src], s)
                macd_line = [efast[i] - eslow[i] for i in range(len(efast))]
                sigl = ema(macd_line, sig)
                series_cache[name] = [macd_line[i] - sigl[i] for i in range(len(macd_line))]
            elif kind == "stoch_k":
                klen, dlen = int(spec[3]), int(spec[4])
                # %K = 100 * (close - LL(klen)) / (HH(klen) - LL(klen))
                k_list: List[float] = []
                for i in range(len(closes)):
                    start = max(0, i - klen + 1)
                    hh = max(highs[start:i+1])
                    ll = min(lows[start:i+1])
                    denom = (hh - ll) or 1e-9
                    k_list.append(100.0 * (closes[i] - ll) / denom)
                # Smooth %K by simple SMA of length spec[2] (smooth)
                smooth = int(spec[2])
                if smooth > 1:
                    k_sm = st.sma(k_list, smooth)
                else:
                    k_sm = k_list
                series_cache[name] = k_sm
            elif kind == "stoch_d":
                klen, dlen = int(spec[3]), int(spec[4])
                # D = SMA(K, dlen)
                base_k = series_cache.get(spec[5])  # reference K series name passed in spec[5]
                if base_k is None:
                    # fallback compute similarly
                    tmp = series_cache.get("stoch_k", [math.nan]*len(closes))
                    series_cache[name] = st.sma(tmp, dlen)
                else:
                    series_cache[name] = st.sma(base_k, dlen)
            elif kind == "supertrend":
                factor, per = float(spec[1]), int(spec[2])
                atrv = atr(highs, lows, closes, per)
                out: List[float] = []
                dir_list: List[float] = []
                dirv = 1
                prev_up = prev_dn = 0.0
                for i in range(len(closes)):
                    hl2 = (highs[i] + lows[i]) / 2.0
                    up = hl2 + factor * atrv[i]
                    dn = hl2 - factor * atrv[i]
                    if i == 0:
                        prev_up, prev_dn = up, dn
                    # Toggle on cross
                    if closes[i] > prev_up:
                        dirv = 1
                    elif closes[i] < prev_dn:
                        dirv = -1
                    st_line = dn if dirv == 1 else up
                    out.append(st_line)
                    dir_list.append(dirv)
                    prev_up, prev_dn = up, dn
                series_cache[name] = out
                # Store direction series if provided
                dname = spec[3] if len(spec) > 3 else None
                if dname:
                    series_cache[dname] = dir_list
            else:
                series_cache[name] = [math.nan] * len(closes)

        # evaluate rules → position
        pos = [0] * len(closes)
        holding = False
        trades: List[Dict[str, Any]] = []

        def crossed_up(a: List[float], b: List[float], i: int) -> bool:
            if i < 1 or any(math.isnan(x) for x in (a[i], b[i], a[i-1], b[i-1])):
                return False
            return a[i-1] <= b[i-1] and a[i] > b[i]

        def crossed_dn(a: List[float], b: List[float], i: int) -> bool:
            if i < 1 or any(math.isnan(x) for x in (a[i], b[i], a[i-1], b[i-1])):
                return False
            return a[i-1] >= b[i-1] and a[i] < b[i]

        for i in range(len(closes)):
            entry_fire = False
            close_fire = False
            for r in self.rules:
                cond = r["cond"]
                ok = False
                if cond[0] == "crossover":
                    sa, sb = series_cache[cond[1]], series_cache[cond[2]]
                    ok = crossed_up(sa, sb, i)
                elif cond[0] == "crossunder":
                    sa, sb = series_cache[cond[1]], series_cache[cond[2]]
                    ok = crossed_dn(sa, sb, i)
                elif cond[0] == "cmp":
                    sname, op, val = cond[1], cond[2], float(cond[3])
                    v = series_cache.get(sname, [math.nan] * len(closes))[i]
                    if not math.isnan(v):
                        if op == "<": ok = v < val
                        elif op == ">": ok = v > val
                        elif op == "<=": ok = v <= val
                        elif op == ">=": ok = v >= val
                if not ok:
                    continue
                if r["type"] == "entry":
                    entry_fire = True
                else:
                    close_fire = True
            if holding and close_fire:
                holding = False
                trades.append({"ts": candles[i]["time"], "side": "sell", "price": closes[i]})
            if (not holding) and entry_fire:
                holding = True
                trades.append({"ts": candles[i]["time"], "side": "buy", "price": closes[i]})
            pos[i] = 1 if holding else 0

        rets, total, mdd = st.evaluate_position_returns(closes, pos)
        sh = st.sharpe_ratio(rets)
        return st.BacktestResult(self.name, total, sh, mdd, trades, details={"params": self.params})


def compile_pine(code: str) -> CompiledStrategy:
    lines = [ln.strip() for ln in code.splitlines() if ln.strip() and not ln.strip().startswith("//")]
    params: Dict[str, Any] = {}
    series: Dict[str, Any] = {}
    rules: List[Dict[str, Any]] = []

    def parse_num(tok: str) -> float:
        return float(tok) if "." in tok else float(int(tok))

    # inputs
    input_re = re.compile(r"(\w+)\s*=\s*input\.(?:int|float)\(([^\)]*)\)")
    # single-output indicators
    ind_re = re.compile(r"(\w+)\s*=\s*ta\.(sma|ema|rsi)\(([^,\)]+)\s*,\s*([^\)]+)\)")
    # multi-output indicators
    bb_re = re.compile(r"\[\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\]\s*=\s*ta\.(?:bb|bbands)\(([^,]+)\s*,\s*([^,]+)\s*,\s*([^\)]+)\)")
    macd_re = re.compile(r"\[\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\]\s*=\s*ta\.macd\(([^,]+)\s*,\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^\)]+)\)")
    stoch_re = re.compile(r"\[\s*(\w+)\s*,\s*(\w+)\s*\]\s*=\s*ta\.stoch\(([^,]+)\s*,\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^\)]+)\)")
    super_re = re.compile(r"\[\s*(\w+)\s*,\s*(\w+)\s*\]\s*=\s*ta\.supertrend\(([^,]+)\s*,\s*([^\)]+)\)")
    # rules
    cross_re = re.compile(r"if\s+ta\.(crossover|crossunder)\(([^,]+)\s*,\s*([^\)]+)\)\s*:\s*strategy\.(entry|close)\(")
    cmp_re = re.compile(r"if\s+(\w+)\s*(<=|>=|<|>)\s*([-+]?[0-9]*\.?[0-9]+)\s*:\s*strategy\.(entry|close)\(")

    strategy_name = "PineStrategy"

    for ln in lines:
        if ln.startswith("strategy("):
            m = re.search(r"title\s*=\s*\"([^\"]+)\"", ln)
            if m:
                strategy_name = m.group(1)
            continue
        m = input_re.match(ln)
        if m:
            name, args = m.group(1), m.group(2)
            nums = re.findall(r"[-+]?[0-9]*\.?[0-9]+", args)
            if nums:
                v = parse_num(nums[0])
                params[name] = v
            continue
        m = ind_re.match(ln)
        if m:
            name, kind, src, n = m.group(1), m.group(2), m.group(3).strip(), m.group(4).strip()
            series[name] = (kind, src, n)
            continue
        m = bb_re.match(ln)
        if m:
            basis, upper, lower, src, n, mult = m.groups()
            series[basis] = ("bb_basis", src.strip(), n.strip(), mult.strip())
            series[upper] = ("bb_upper", src.strip(), n.strip(), mult.strip())
            series[lower] = ("bb_lower", src.strip(), n.strip(), mult.strip())
            continue
        m = macd_re.match(ln)
        if m:
            macd_name, sig_name, hist_name, src, f, s, sig = m.groups()
            for nm, kind in ((macd_name, "macd"), (sig_name, "macd_signal"), (hist_name, "macd_hist")):
                series[nm] = (kind, src.strip(), f.strip(), s.strip(), sig.strip())
            continue
        m = stoch_re.match(ln)
        if m:
            kname, dname, hi, lo, cl, smooth, dlen = m.groups()
            series[kname] = ("stoch_k", hi.strip(), lo.strip(), int(smooth), int(dlen))
            # pass reference name of K for D
            series[dname] = ("stoch_d", hi.strip(), lo.strip(), int(smooth), int(dlen), kname)
            continue
        m = super_re.match(ln)
        if m:
            stname, dirname, factor, per = m.groups()
            series[stname] = ("supertrend", float(factor), int(per), dirname)
            continue
        m = cross_re.match(ln)
        if m:
            op, a, b, action = m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4)
            rules.append({"type": "entry" if action == "entry" else "close", "cond": (op, a, b)})
            continue
        m = cmp_re.match(ln)
        if m:
            sname, op, num, action = m.group(1), m.group(2), m.group(3), m.group(4)
            rules.append({"type": "entry" if action == "entry" else "close", "cond": ("cmp", sname, op, num)})
            continue
        # ignore the rest

    # Fallback MA cross if no rules present
    if not rules:
        ma_names = [k for k, v in series.items() if v[0] in ("sma", "ema")]
        if len(ma_names) >= 2:
            rules.append({"type": "entry", "cond": ("crossover", ma_names[0], ma_names[1])})
            rules.append({"type": "close", "cond": ("crossunder", ma_names[0], ma_names[1])})

    return CompiledStrategy(name=strategy_name, params=params, series=series, rules=rules)

