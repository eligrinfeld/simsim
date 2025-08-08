from __future__ import annotations
import os
from datetime import datetime
from typing import Optional


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def resolve_artifacts_path(cfg_outputs: dict) -> str:
    pattern = cfg_outputs.get("path", "artifacts/run_{date}")
    today = datetime.now().strftime("%Y%m%d")
    return pattern.format(date=today)


def write_parquet_or_csv(df, path: str) -> str:
    """
    Attempt to write parquet; if engine missing, write CSV instead.
    Returns the actual written file path.
    """
    ensure_dir(os.path.dirname(path) or ".")
    try:
        df.to_parquet(path, index=False)
        return path
    except Exception:
        # Fallback to CSV
        alt = path[:-8] + ".csv" if path.endswith(".parquet") else path + ".csv"
        df.to_csv(alt, index=False)
        return alt


def write_series_parquet_or_csv(series, path: str, name: Optional[str] = None) -> str:
    # Include index as columns so downstream readers can recover labels (e.g., tickers)
    import pandas as pd  # local import to avoid global dependency during tests

    df = series.to_frame(name=name or series.name or "value")
    # Ensure unique index level names before reset_index() to avoid collisions like 'Ticker','Ticker'
    if isinstance(df.index, pd.MultiIndex):
        new_names = []
        seen = set()
        for i, nm in enumerate(df.index.names):
            nm = nm or f"level_{i}"
            if nm in seen:
                nm = f"{nm}_{i}"
            seen.add(nm)
            new_names.append(nm)
        df.index = df.index.set_names(new_names)
    return write_parquet_or_csv(df.reset_index(), path)
