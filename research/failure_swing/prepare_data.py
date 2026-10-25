"""Downloads Bitstamp BTC/USD 1-minute candles (github.com/ff137/bitstamp-btcusd-minute-data),
keeps 2017 onwards and saves them as data/min.npz for bt.py. Then run baseline.py first (builds bars.pkl)."""
import os
import urllib.request

import numpy as np
import pandas as pd

BASE = "https://raw.githubusercontent.com/ff137/bitstamp-btcusd-minute-data/main/data/"
FILES = {"hist.csv.gz": "historical/btcusd_bitstamp_1min_2012-2025.csv.gz",
         "latest.csv": "updates/btcusd_bitstamp_1min_latest.csv"}
OUT = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
COLS = ["timestamp", "open", "high", "low", "close"]

os.makedirs(OUT, exist_ok=True)
for name, path in FILES.items():
    if not os.path.exists(os.path.join(OUT, name)):
        urllib.request.urlretrieve(BASE + path, os.path.join(OUT, name))
a = pd.read_csv(os.path.join(OUT, "hist.csv.gz"), usecols=COLS)
a = a[a.timestamp >= pd.Timestamp("2017-01-01", tz="UTC").timestamp()]
b = pd.read_csv(os.path.join(OUT, "latest.csv"), usecols=COLS)
m = pd.concat([a, b]).drop_duplicates("timestamp").sort_values("timestamp")
np.savez(os.path.join(OUT, "min.npz"), **{c: m[c].values for c in COLS})
