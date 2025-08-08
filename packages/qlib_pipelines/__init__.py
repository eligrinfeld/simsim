from __future__ import annotations
import os


def write_qlib_dataset(df, root: str = "./features/qlib"):
    os.makedirs(root, exist_ok=True)
    # For now, write a minimal CSV to signal dataset creation
    out = os.path.join(root, "prices_sample.csv")
    # Avoid heavy writes; just head(5)
    try:
        df.reset_index().head(5).to_csv(out, index=False)
    except Exception:
        pass


def train_factor_model(config: dict):
    # Placeholder training stub
    return {"status": "ok"}
