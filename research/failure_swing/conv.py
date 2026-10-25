import sys, glob, numpy as np, pandas as pd
src, out = sys.argv[1], sys.argv[2]
fs = sorted(glob.glob(f"{src}/1m/*/*/*.csv"))
d = pd.concat([pd.read_csv(f, usecols=["timestamp","open","high","low","close","volume"]) for f in fs])
d["timestamp"] = (d.timestamp // 1000).astype(np.int64)
d = d.drop_duplicates("timestamp").sort_values("timestamp")
# fill missing minutes with flat zero-volume candles (exchange downtime), as in the Bitstamp set
full = np.arange(d.timestamp.iloc[0], d.timestamp.iloc[-1] + 60, 60)
d = d.set_index("timestamp").reindex(full)
gaps = d.close.isna().sum()
d["close"] = d.close.ffill()
for c in ["open","high","low"]: d[c] = d[c].fillna(d.close)
d["volume"] = d.volume.fillna(0)
np.savez(out, timestamp=full, **{c: d[c].values.astype(np.float64) for c in ["open","high","low","close","volume"]})
print(src.split('/')[-1], len(fs), "files", len(d), "minutes", gaps, "filled", pd.to_datetime(full[[0,-1]], unit="s").tolist())
