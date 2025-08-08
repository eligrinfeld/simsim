import pandas as pd
from packages.portfolio_toolkit import optimize

def test_optimize_respects_top_k_and_cap():
  scores = pd.Series({"A": 0.9, "B": 0.8, "C": 0.7, "D": 0.1, "E": -0.2})
  w = optimize(scores, constraints={"top_k": 3, "cap_per_name": 0.4})
  # Use at most top_k names
  assert (w > 0).sum() <= 3
  # Cap should be respected
  assert w.max() <= 0.4 + 1e-9
  # Weights sum to 1
  assert abs(w.sum() - 1.0) < 1e-9

