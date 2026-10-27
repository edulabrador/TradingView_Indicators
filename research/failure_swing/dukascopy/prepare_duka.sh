#!/usr/bin/env bash
# Dukascopy 1-minute BID candles for BTCUSD and XAUUSD (2022-01 -> 2026-08), as mirrored in
# github.com/meffyou226-oss/Meffs (downloaded there with dukascopy-node). Builds data/duka4h.pkl and data/DUKA_*.npz.
# Direct download from datafeed.dukascopy.com is the alternative when the network allows it.
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p data tmp
[ -d tmp/meffs ] || git clone -q --depth 1 --filter=blob:none --no-checkout https://github.com/meffyou226-oss/Meffs tmp/meffs
(cd tmp/meffs && git checkout -q HEAD -- data/btcusd_m1 data/xauusd_m1)
python3 -c "
import sys, pickle; sys.path.insert(0, '.')
import duka
X = {s: duka.bars4h(s)[0] for s in ['BTCUSD', 'XAUUSD']}
pickle.dump(X, open('data/duka4h.pkl', 'wb'))
for s in X: duka.to_npz(s, f'data/DUKA_{s}.npz')
"
