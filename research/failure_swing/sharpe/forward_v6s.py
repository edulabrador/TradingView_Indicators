"""Forward test of portfolio V6 spot from FORWARD_START (see ../FORWARD_TEST.md). Run ../prepare_alts.sh first."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import portfolio_v6s as portfolio_a
FORWARD_START = "2026-10-27"
if __name__ == "__main__":
    r = portfolio_a.build(refresh=True)
    last = r.index[-1]
    r = r[r.index >= pd.Timestamp(FORWARD_START, tz="UTC")]
    d = (1 + r).groupby(r.index.floor("1D")).prod() - 1
    if len(d) < 2:
        print(f"no forward data yet (last bar {last})"); sys.exit(0)
    eq = (1 + d).cumprod()
    print(f"days {len(d)}  return {eq.iloc[-1] - 1:+.3f}  Sharpe {d.mean() / d.std() * np.sqrt(365):.2f}  max DD {(eq / eq.cummax() - 1).min():.3f}")
