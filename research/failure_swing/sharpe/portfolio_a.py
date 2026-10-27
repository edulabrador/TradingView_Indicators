"""Portfolio A: S/R breakout (4h, period 84, trail 4 ATR, SMA 50 days, long+short) on the 12 Binance pairs,
equal risk per asset (target 50% / vol30d / N, gross cap 2x, resized daily), whole portfolio scaled to 25% annual
vol (30-day lookback, cap 3x, resized daily). 0.15% per side on every notional traded."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
import numpy as np, pandas as pd
import assets

UNIV = ["BTC", "ETH", "SOL", "BNB", "XRP", "LTC", "ADA", "DOGE", "LINK", "TRX", "AVAX", "DOT"]


def build(refresh=True):
    import port as P
    P.A = assets.load_all(refresh=refresh, names=UNIV)
    P.UNIV = UNIV
    U = {a: P.unit_returns(P.A[a]) for a in UNIV}
    R, Pos, Al = (pd.concat({a: u[j] for a, u in U.items()}, axis=1) for j in range(3))
    r, g = P.combine(R, Pos, Al, "risk", P.asset_vol(30), target=0.5, cap=2.0)
    v = r.rolling(30 * 6, min_periods=10 * 6).std().shift(1) * np.sqrt(P.BPY)
    s = (0.25 / v).clip(upper=3.0).fillna(0)
    s = s.where(pd.Series(np.arange(len(s)) % 6 == 0, s.index), np.nan).ffill().fillna(0)
    return s * r - P.COST * (s - s.shift(1).fillna(0)).abs() * g.shift(1).fillna(0)


if __name__ == "__main__":
    import port as P
    r = build(refresh=False)
    print("A:", P.stats(r))
