"""Portfolio V6 spot: long-only S/R breakout (4h, 84, trail 4 ATR, SMA 50d) + long-only time-series momentum
(share of positive 7/30/90-day returns), each sized per asset at 50% / vol30d / N (breakout gross cap 2x),
the two legs combined at equal risk (90-day sleeve vol), whole portfolio scaled to 25% annual vol with a 1x
gross cap (no leverage), everything resized daily, 0.15% per side on every notional traded."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
import numpy as np, pandas as pd
import assets
from portfolio_a import UNIV


def build(refresh=True):
    import port as P
    P.A = assets.load_all(refresh=refresh, names=UNIV); P.UNIV = UNIV
    U = {a: P.unit_returns(P.A[a], side="long") for a in UNIV}
    R, Pos, Al = (pd.concat({a: u[j] for a, u in U.items()}, axis=1) for j in range(3))
    V = P.asset_vol(30)
    C = P.frame(lambda a: pd.Series(P.A[a]["c"], P.A[a]["idx"])); ret = C.pct_change().fillna(0)
    AlB = Al.fillna(False); N = AlB.sum(axis=1).replace(0, np.nan)
    step = lambda W, reb=6: W.where(pd.Series(np.arange(len(W)) % reb == 0, W.index), np.nan).ffill().fillna(0)
    bo = P.combine(R, Pos, Al, "risk", V, target=0.5, cap=2.0)
    sig = (sum(np.sign(C / C.shift(L * 6) - 1) for L in (7, 30, 90)) / 3).clip(lower=0)
    W = step((sig * (0.5 / V)).where(AlB).div(N, axis=0)); Wl = W.shift(1).fillna(0)
    ts = ((Wl * ret).sum(axis=1) - P.COST * (Wl - Wl.shift(1).fillna(0)).abs().sum(axis=1)
          - P.COST * (Wl.abs() * ret.abs()).sum(axis=1), Wl.abs().sum(axis=1))
    X = pd.concat({"bo": bo[0], "ts": ts[0]}, axis=1); G = pd.concat({"bo": bo[1], "ts": ts[1]}, axis=1)
    v = X.rolling(90 * 6, min_periods=180).std().shift(1); w = step((1 / v).div((1 / v).sum(axis=1), axis=0).fillna(0))
    r, g = (w * X).sum(axis=1), (w * G).sum(axis=1)
    pv = r.rolling(30 * 6, min_periods=60).std().shift(1) * np.sqrt(P.BPY)
    s = step((0.25 / pv).clip(upper=1.0).fillna(0))
    return s * r - P.COST * (s - s.shift(1).fillna(0)).abs() * g.shift(1).fillna(0)


if __name__ == "__main__":
    import port as P
    print("V6 spot:", P.stats(build(refresh=False)))
