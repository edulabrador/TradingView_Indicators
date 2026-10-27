"""Forward test of the R2a Pine strategy on two baskets of charts (equal capital, monthly rebalance), from
FORWARD_START (see ../FORWARD_TEST.md). Run ../prepare_alts.sh first."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, ".."), os.path.join(HERE, "..", "sharpe")):
    sys.path.insert(0, p)
import numpy as np, pandas as pd
import assets, single
FORWARD_START = "2026-10-27"
R2A = dict(mint=0.10, mom_mode="cont")
BASKETS = {"BTC+ETH": ["BTC", "ETH"], "top-5": ["BTC", "ETH", "BNB", "SOL", "XRP"]}


def basket(names, A, start=None):
    E = {n: single.run(A[n], cost=0.0015, **R2A) for n in names}
    R = pd.concat({n: e.pct_change() for n, e in E.items()}, axis=1).dropna()
    if start:
        R = R[R.index >= pd.Timestamp(start, tz="UTC")]
    v = np.ones(len(names)) / len(names); out = []
    for _, g in R.groupby(R.index.strftime("%Y-%m")):
        for _, row in g.iterrows():
            v = v * (1 + row.values); out.append(v.sum())
        v = np.ones(len(names)) * v.sum() / len(names)
    return pd.Series(out, R.index)


if __name__ == "__main__":
    A = assets.load_all(refresh=True, names=sorted({n for v in BASKETS.values() for n in v}))
    for k, names in BASKETS.items():
        eq = basket(names, A, FORWARD_START)
        if len(eq) < 2:
            print(f"{k}: no forward data yet (last bar {A['BTC']['idx'][-1]})"); continue
        d = eq.pct_change().dropna()
        print(f"{k}: days {len(eq)}  return {eq.iloc[-1] - 1:+.3f}  Sharpe {d.mean() / d.std() * np.sqrt(365):.2f}  max DD {(eq / eq.cummax() - 1).min():.3f}")
