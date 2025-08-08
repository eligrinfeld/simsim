import pandas as pd


def run_optimization(df, sigs, sent, cfg):
    score = sigs["mom_20"].copy().fillna(-1e9)
    k = int(cfg.get("top_k", 5))
    cap = float(cfg.get("constraints", {}).get("cap_per_name", 0.25))

    picks = score.nlargest(k).index
    w = pd.Series(0.0, index=score.index)
    if len(picks) > 0:
        w.loc[picks] = 1.0 / len(picks)

    w = w.clip(upper=cap)
    w = w / (w.sum() or 1.0)
    return w
