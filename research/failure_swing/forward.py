"""Forward test of the frozen S/R breakout rules on the 12 assets, from FORWARD_START onwards (see FORWARD_TEST.md).
Run ./prepare_alts.sh first to fetch the latest candles."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cross, eng, pandas as pd, numpy as np
FORWARD_START = "2026-10-25"
if __name__ == "__main__":
    rows, curves, trades = [], {}, []
    for a in cross.ASSETS:
        b, _ = cross.load(a)
        if b.index[-1] < pd.Timestamp(FORWARD_START, tz="UTC"):
            print(f"{a}: no bars after {FORWARD_START} yet (last bar {b.index[-1]})")
            continue
        # indicators warm up on history; only trades opened from FORWARD_START count
        tr, cv = cross.ev(b, FORWARD_START, None)
        st = eng.stats(tr, cv) if len(cv) > 1 else {}
        rows.append(dict(asset=a, last_bar=b.index[-1], n=len(tr), ret=tr.ret.sum(), **{k: st.get(k) for k in ["pf", "net", "dd"]}))
        curves[a] = cv.resample("1D").last(); trades.append(tr.assign(asset=a))
    if not rows:
        print("no forward data yet: nothing to evaluate"); sys.exit(0)
    df = pd.DataFrame(rows); T = pd.concat(trades); r = T.ret
    P = pd.concat({a: c / c.iloc[0] for a, c in curves.items() if len(c)}, axis=1).ffill().mean(axis=1)
    pd.set_option("display.width", 200); pd.set_option("display.float_format", "{:.3f}".format)
    print(df.to_string(index=False))
    t = r.mean() / r.std(ddof=1) * np.sqrt(len(r)) if len(r) > 2 else float("nan")
    print(f"pooled trades {len(r)}  mean {r.mean():.4f}  t {t:.2f}")
    print(f"portfolio return {P.iloc[-1] - 1:.3f}  max DD {(P / P.cummax() - 1).min():.3f}  days {(P.index[-1] - P.index[0]).days}")
