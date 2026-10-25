import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cross, eng, pandas as pd, numpy as np
from multiprocessing import Pool
def one(a):
    b, start = cross.load(a); out = {}
    for cost in [0.0015, 0.0025]:
        cross.COST = cost; tr, cv = cross.ev(b, start, cross.END); st = eng.stats(tr, cv)
        out[cost] = (st["cagr"], st["pf"])
    cross.COST = 0.0015; tr, cv = cross.ev(b, "2020-11-21", cross.END)
    px = b.close[b.index >= pd.Timestamp("2020-11-21", tz="UTC")]
    return a, out, cv.resample("1D").last(), px.resample("1D").last()
if __name__ == "__main__":
    with Pool(4) as P: R = P.map(one, cross.ASSETS)
    print("asset  cagr@0.15%  pf@0.15%  cagr@0.25%  pf@0.25%")
    for a, o, _, _ in R: print(f"{a:5s} {o[0.0015][0]:9.3f} {o[0.0015][1]:8.2f} {o[0.0025][0]:10.3f} {o[0.0025][1]:8.2f}")
    print("profitable at 0.25% (ex BTC):", sum(o[0.0025][0] > 0 and o[0.0025][1] > 1 for a, o, _, _ in R if a != "BTC"), "of 11")
    S = pd.concat({a: cv / cv.iloc[0] for a, _, cv, _ in R}, axis=1).ffill().mean(axis=1)
    H = pd.concat({a: p / p.iloc[0] for a, _, _, p in R}, axis=1).ffill().mean(axis=1)
    def m(x, a=None, e=None):
        x = x[a:e] if a else x; x = x / x.iloc[0]; y = (x.index[-1] - x.index[0]).days / 365.25; d = x.pct_change().dropna()
        return "CAGR %.1f%%  DD %.1f%%  Sharpe %.2f" % (100 * (x.iloc[-1] ** (1 / y) - 1), 100 * (x / x.cummax() - 1).min(), d.mean() / d.std() * np.sqrt(365))
    print("equal-weight portfolio 2020-11-21 -> 2026-10, 12 sleeves, no rebalancing")
    print(" strategy:", m(S)); print(" buy&hold:", m(H))
    print(" 2025-26 strategy:", m(S, "2025-01-01")); print(" 2025-26 buy&hold:", m(H, "2025-01-01"))
    ye = S.resample("YE").last(); print((ye / ye.shift(1).fillna(1) - 1).round(3).to_string())
