"""Backtester for the Failure Swing strategy, replicating TradingView's broker emulator.

mode="v3": original script. Exits are strategy.close() evaluated at bar close -> filled next open.
mode="v6": ported script. Exits are stop/limit orders placed at bar close, filled intrabar on the
           next bar. Intrabar path resolved with 1-minute data (intrabar="minute") or with
           TradingView's OHLC heuristic (intrabar="ohlc").
"""
import os

import numpy as np
import pandas as pd

DATA = os.path.join(os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data")), "min.npz")
_M = None


def minutes():
    global _M
    if _M is None:
        z = np.load(DATA)
        _M = {k: z[k] for k in z.files}
    return _M


def bars(tf):
    """Resample 1-minute data to tf (pandas rule, e.g. '4h'). Returns DataFrame with minute index bounds."""
    m = minutes()
    idx = pd.to_datetime(m["timestamp"], unit="s", utc=True)
    df = pd.DataFrame({k: m[k] for k in ["open", "high", "low", "close"]}, index=idx)
    df["i"] = np.arange(len(df))
    g = df.resample(tf, label="left", closed="left")
    b = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                      "close": g["close"].last(), "i0": g["i"].min(), "i1": g["i"].max() + 1}).dropna()
    b[["i0", "i1"]] = b[["i0", "i1"]].astype(np.int64)
    return b


def indicators(b, period=84, ema_len=120, threshold=5.0, coef_tp=0.05, coef_sl=0.02, sl_pct=2.0,
               ema_side=True, start="2018-08-01", end=None):
    o, h, l, c = b.open, b.high, b.low, b.close
    res = h.shift(1).rolling(period).max()
    sup = l.shift(1).rolling(period).min()
    ema = c.ewm(span=ema_len, adjust=False).mean()
    vol = (o - ema).abs() / ema
    tp = ema * (1 + vol * coef_tp * np.sign(o - ema))
    in_range = b.index >= pd.Timestamp(start, tz="UTC")
    if end is not None:
        in_range &= b.index < pd.Timestamp(end, tz="UTC")
    vol_ok = vol > threshold / 100
    short = in_range & vol_ok & (res.shift(1) == res.shift(2)) & (h >= res.shift(1)) & (c < res.shift(1))
    long_ = in_range & vol_ok & (sup.shift(1) == sup.shift(2)) & (l <= sup.shift(1)) & (c > sup.shift(1))
    if ema_side:
        short &= tp < c
        long_ &= tp > c
    return dict(o=o.values, h=h.values, l=l.values, c=c.values, tp=tp.values, vol=vol.values,
                long=long_.values, short=short.values, sl=sl_pct / 100, coef_sl=coef_sl,
                i0=b.i0.values, i1=b.i1.values, t=b.index)


def _scan_minutes(i0, i1, d, stop, limit, start_px):
    """First fill of a stop/limit pair inside minutes [i0, i1). Returns (price, reason) or None.
    Same-minute ambiguity resolved stop-first (conservative)."""
    m = minutes()
    lo, hi, op = m["low"][i0:i1], m["high"][i0:i1], m["open"][i0:i1]
    if d > 0:
        hs = lo <= stop if not np.isnan(stop) else np.zeros(len(lo), bool)
        hl = hi >= limit if not np.isnan(limit) else np.zeros(len(lo), bool)
    else:
        hs = hi >= stop if not np.isnan(stop) else np.zeros(len(lo), bool)
        hl = lo <= limit if not np.isnan(limit) else np.zeros(len(lo), bool)
    any_ = hs | hl
    if not any_.any():
        return None
    k = int(np.argmax(any_))
    # first minute: the bar open is the fill reference (gap through the level fills at the open)
    ref = start_px if k == 0 else op[k]
    if hs[k]:
        return (min(stop, ref) if d > 0 else max(stop, ref)), "SL"
    return (max(limit, ref) if d > 0 else min(limit, ref)), "TP"


def _scan_ohlc(o, h, l, d, stop, limit):
    """TradingView default intrabar assumption: open -> nearest extreme -> other extreme -> close."""
    path = [o, h, l] if abs(h - o) < abs(o - l) else [o, l, h]
    for a, z in zip(path[:-1], path[1:]):
        for lvl, reason in ((stop, "SL"), (limit, "TP")):
            if np.isnan(lvl):
                continue
            if d > 0 and reason == "SL" and min(a, z) <= lvl:
                return min(lvl, a), reason
            if d > 0 and reason == "TP" and max(a, z) >= lvl:
                return max(lvl, a), reason
            if d < 0 and reason == "SL" and max(a, z) >= lvl:
                return max(lvl, a), reason
            if d < 0 and reason == "TP" and min(a, z) <= lvl:
                return min(lvl, a), reason
    return None


def run(ind, mode="v6", intrabar="minute", commission=0.2, slippage=0.0, capital=1000.0,
        allow_short=True, random_signals=None):
    """Returns (trades DataFrame, equity Series at bar close)."""
    o, h, l, c, tp, vol = ind["o"], ind["h"], ind["l"], ind["c"], ind["tp"], ind["vol"]
    longs, shorts = ind["long"], ind["short"]
    if random_signals is not None:
        longs, shorts = random_signals
    sl, csl = ind["sl"], ind["coef_sl"]
    fee, slip = commission / 100, slippage / 100
    n = len(o)
    cash = capital          # realised equity
    pos = 0; qty = 0.0; entry = np.nan; t_in = None
    pending = None          # (dir, qty) market entry for next open
    pend_close = False      # v3: close at next open
    lv = None               # v6: (stop_long, tp, stop_short, tp) active this bar
    trades, eq = [], np.empty(n)

    def close_at(px, i, reason):
        nonlocal cash, pos, qty, entry
        px = px * (1 - slip * pos)
        pnl = pos * qty * (px - entry) - fee * qty * px
        cash += pnl
        trades.append((t_in, ind["t"][i], pos, entry, px, pnl, reason))
        pos = 0; qty = 0.0; entry = np.nan

    for i in range(n):
        # 1) orders sent at previous close fill at this open
        if pending is not None:
            d, q = pending
            if pos != d:
                if pos != 0:
                    close_at(o[i], i, "reverse")
                if d != 0:
                    pos = d; qty = q
                    entry = o[i] * (1 + slip * d)
                    cash -= fee * qty * entry
                    t_in = ind["t"][i]
            pending = None
        if pend_close and pos != 0:
            close_at(o[i], i, "exit")
        pend_close = False
        # 2) v6 intrabar stop/limit
        if mode == "v6" and pos != 0 and lv is not None:
            stop, limit = (lv[0], lv[1]) if pos > 0 else (lv[2], lv[3])
            if intrabar == "minute":
                r = _scan_minutes(ind["i0"][i], ind["i1"][i], pos, stop, limit, o[i])
            else:
                r = _scan_ohlc(o[i], h[i], l[i], pos, stop, limit)
            if r is not None:
                close_at(r[0], i, r[1])
        # 3) logic at bar close
        equity = cash + (pos * qty * (c[i] - entry) if pos else 0.0)
        eq[i] = equity
        new_dir = 0
        if longs[i]:
            new_dir = 1          # long block runs after short block in the script
        elif shorts[i]:
            new_dir = -1
        if new_dir == -1 and not allow_short:
            new_dir = 0 if pos <= 0 else -2   # long-only: short signal just closes a long
        if new_dir == -2:
            pend_close = True
        elif new_dir != 0 and new_dir != pos:
            pending = (new_dir, equity / c[i])
        if mode == "v3":
            if pos > 0 and (l[i] < entry * (1 - sl - vol[i] * csl) or h[i] > tp[i]):
                pend_close = pending is None
            if pos < 0 and (h[i] > entry * (1 + sl + vol[i] * csl) or l[i] < tp[i]):
                pend_close = pending is None
            lv = None
        else:
            ref_l = c[i] if (new_dir == 1 and pos <= 0) else entry
            ref_s = c[i] if (new_dir == -1 and pos >= 0) else entry
            lv = (ref_l * (1 - sl - vol[i] * csl), tp[i], ref_s * (1 + sl + vol[i] * csl), tp[i])
    tr = pd.DataFrame(trades, columns=["t_in", "t_out", "dir", "entry", "exit", "pnl", "reason"])
    return tr, pd.Series(eq, index=ind["t"])


def stats(tr, eq, capital=1000.0, start="2018-08-01"):
    eq = eq[eq.index >= pd.Timestamp(start, tz="UTC")]
    years = (eq.index[-1] - eq.index[0]).days / 365.25
    final = eq.iloc[-1]
    dd = (eq / eq.cummax() - 1).min()
    wins = tr.pnl[tr.pnl > 0].sum(); losses = -tr.pnl[tr.pnl < 0].sum()
    ret_tr = tr.dir * (tr.exit / tr.entry - 1)
    return dict(trades=len(tr), win=(tr.pnl > 0).mean() if len(tr) else np.nan,
                pf=wins / losses if losses > 0 else np.nan, net=final / capital - 1,
                cagr=(final / capital) ** (1 / years) - 1 if final > 0 else -1, maxdd=dd,
                avg_tr=ret_tr.mean() if len(tr) else np.nan)
