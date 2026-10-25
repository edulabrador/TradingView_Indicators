"""Frozen S/R breakout rules on other assets (see PREREG_cross.md)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eng, strat, pandas as pd, numpy as np
from multiprocessing import Pool
CFG = dict(period=84, side="both", trail_k=4, trend_days=50); TF = "4h"; COST = 0.0015
DD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
ASSETS = ["ETH", "SOL", "BNB", "XRP", "LTC", "ADA", "DOGE", "LINK", "TRX", "AVAX", "DOT", "BTC"]
END = "2026-10-25"

def load(a):
    eng.DATA = os.path.join(DD, f"{a}USDT.npz"); eng._M = None
    b = eng.bars(TF); return b, (b.index[0] + pd.Timedelta(days=60)).strftime("%Y-%m-%d")

def ev(b, start, end, sig=None):
    s = strat.breakout(b, TF, **CFG)
    if sig is not None:
        c = b.close.values; at = strat.atr(b).values
        s["sig"] = sig; s["stop"] = np.where(sig > 0, c - CFG["trail_k"] * at, c + CFG["trail_k"] * at)
    return eng.run(b, s["sig"], s["stop"], None, None, s["hold"], start=start, end=end, trail=s["trail"],
                   reverse=True, cost=COST)

def bh(b, start, end):
    x = b.close[(b.index >= start) & (b.index < end)]; yrs = (x.index[-1] - x.index[0]).days / 365.25
    d = x.resample("1D").last().pct_change().dropna()
    return dict(bh_cagr=(x.iloc[-1] / x.iloc[0]) ** (1 / yrs) - 1, bh_dd=(x / x.cummax() - 1).min(),
                bh_sharpe=d.mean() / d.std() * np.sqrt(365))

def asset(a, ndraw=200):
    b, start = load(a); out = []
    for w, (s0, e0) in {"full": (start, END), "2025-26": (max(start, "2025-01-01"), END)}.items():
        tr, cv = ev(b, s0, e0); st = eng.stats(tr, cv); st.update(bh(b, pd.Timestamp(s0, tz="UTC"), pd.Timestamp(e0, tz="UTC")))
        st.update(asset=a, window=w, start=s0, sumret=tr.ret.sum())
        if w == "full":
            c = b.close; sma = c.rolling(50 * 6).mean(); T = b.index
            ok = (T >= pd.Timestamp(s0, tz="UTC")) & (T < pd.Timestamp(e0, tz="UTC"))
            up = np.where((c > sma).values & ok)[0]; dn = np.where((c < sma).values & ok)[0]
            nl, ns = (tr.dir > 0).sum(), (tr.dir < 0).sum(); rng = np.random.default_rng(0); R = []
            for _ in range(ndraw):
                sig = np.zeros(len(T), int); sig[rng.choice(up, nl, replace=False)] = 1; sig[rng.choice(dn, ns, replace=False)] = -1
                R.append(ev(b, s0, e0, sig)[0].ret.sum())
            st["rand"] = R; st["p"] = float(np.mean(np.array(R) >= tr.ret.sum()))
        out.append(st)
    return out

if __name__ == "__main__":
    avail = [a for a in ASSETS if os.path.exists(os.path.join(DD, f"{a}USDT.npz"))]
    with Pool(4) as P: res = sum(P.map(asset, avail), [])
    df = pd.DataFrame(res); df.to_pickle("cross.pkl")
    pd.set_option("display.width", 250); pd.set_option("display.float_format", "{:.3f}".format)
    cols = ["asset", "start", "n", "win", "pf", "avg", "t", "cagr", "dd", "sharpe", "bh_cagr", "bh_dd", "bh_sharpe"]
    full = df[df.window == "full"]; print(full[cols + ["p"]].to_string(index=False))
    print(df[df.window == "2025-26"][cols].to_string(index=False))
    ind = full[full.asset != "BTC"]
    print("independent assets", len(ind), "profitable (cagr>0 & pf>1):", int(((ind.cagr > 0) & (ind.pf > 1)).sum()), "median PF %.2f" % ind.pf.median())
    pooled = np.sum(np.vstack(ind.rand.values), axis=0); real = ind.sumret.sum()
    print("pooled random test: real %.2f, random median %.2f, p=%.4f" % (real, np.median(pooled), np.mean(pooled >= real)))
    print("beats B&H sharpe in", int((ind.sharpe > ind.bh_sharpe).sum()), "of", len(ind))
