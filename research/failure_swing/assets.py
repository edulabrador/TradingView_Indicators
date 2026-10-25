"""4h bars for BTC (Bitstamp, from 2014) and the 12 Binance pairs, cached as arrays."""
import os, pickle, numpy as np, pandas as pd
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
NAMES = ["BTC_BS", "BTC", "ETH", "SOL", "BNB", "XRP", "LTC", "ADA", "DOGE", "LINK", "TRX", "AVAX", "DOT"]
def load_all():
    p = os.path.join(D, "bars4h_all.pkl")
    if os.path.exists(p):
        return pickle.load(open(p, "rb"))
    import eng
    out = {}
    for a in NAMES:
        eng.DATA = os.path.join(D, "min_full.npz" if a == "BTC_BS" else f"{a}USDT.npz"); eng._M = None
        b = eng.bars("4h")
        start = pd.Timestamp("2014-01-01", tz="UTC") if a == "BTC_BS" else b.index[0] + pd.Timedelta(days=60)
        out[a] = dict(idx=b.index, o=b.open.values, h=b.high.values, l=b.low.values, c=b.close.values,
                      start=int(np.searchsorted(b.index, start)))
    pickle.dump(out, open(p, "wb"))
    return out
