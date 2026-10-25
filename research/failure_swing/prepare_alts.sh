#!/usr/bin/env bash
# Binance spot 1-minute klines from github.com/parshant231234-eng/<SYMBOL>-Historical-Data -> data/<SYMBOL>.npz
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p data tmp
for s in ETHUSDT SOLUSDT BNBUSDT XRPUSDT LTCUSDT ADAUSDT DOGEUSDT LINKUSDT TRXUSDT AVAXUSDT DOTUSDT BTCUSDT; do
  git clone -q --depth 1 "https://github.com/parshant231234-eng/$s-Historical-Data" "tmp/$s"
  python3 conv.py "tmp/$s" "data/$s.npz"
  rm -rf "tmp/$s"
done
