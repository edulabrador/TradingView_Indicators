"""Dukascopy 1-minute BID candles (github.com/meffyou226-oss/Meffs, downloaded with dukascopy-node) -> 4h bars."""
import glob, os, numpy as np, pandas as pd
SRC = os.environ.get("DUKA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp", "meffs", "data"))
def minutes(sym):
    fs = sorted(glob.glob(os.path.join(SRC, f"{sym.lower()}_m1", "*.csv")))
    d = pd.concat([pd.read_csv(f, dtype=str) for f in fs])
    # one upstream file contains git merge-conflict markers: keep numeric rows only, first copy of each minute
    d = d[d.timestamp.str.fullmatch(r"\d{13}", na=False)].astype({"timestamp": "int64", "open": float, "high": float, "low": float, "close": float})
    d = d.drop_duplicates("timestamp").sort_values("timestamp")
    d.index = pd.to_datetime(d.timestamp, unit="ms", utc=True)
    return d[["open", "high", "low", "close"]]
def bars4h(sym, warm_days=120):
    m = minutes(sym)
    g = m.resample("4h", label="left", closed="left")
    b = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last()}).dropna()
    b = b[b.high > b.low]   # drop filler bars with no price movement (weekends / closed market)
    start = int(np.searchsorted(b.index, b.index[0] + pd.Timedelta(days=warm_days)))
    return dict(idx=b.index, o=b.open.values, h=b.high.values, l=b.low.values, c=b.close.values, start=start), m


def to_npz(sym, path):
    """Minute file in the format of bt.py / eng.py (no volume in the source: zeros)."""
    m = minutes(sym)
    m = m[m.high > m.low] if sym.upper() != "BTCUSD" else m
    np.savez(path, timestamp=((m.index - pd.Timestamp(0, tz="UTC")) // pd.Timedelta(seconds=1)).values.astype("int64"), open=m.open.values, high=m.high.values,
             low=m.low.values, close=m.close.values, volume=np.zeros(len(m)))
