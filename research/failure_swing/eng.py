"""Generic bar-close-signal / next-open-fill engine with intrabar stop/target resolved on 1-minute data.

A strategy supplies, per bar i (evaluated at its close):
  sig[i]   +1 / -1 / 0   entry for the open of bar i+1
  stop[i]  absolute stop price for a position opened at i+1
  tgt[i]   absolute fixed target (nan = none)
  dyn[i]   dynamic target array used while in position (nan = none), level placed at close i for bar i+1
  hold     max bars in position (time stop, exit at open)
"""
import os
import numpy as np
import pandas as pd

DATA = os.environ.get("MIN_DATA", os.path.join(os.path.dirname(__file__), "data", "min_full.npz"))
_M = None


def minutes():
    global _M
    if _M is None:
        z = np.load(DATA)
        _M = {k: z[k] for k in z.files}
    return _M


def bars(tf):
    m = minutes()
    idx = pd.to_datetime(m["timestamp"], unit="s", utc=True)
    df = pd.DataFrame({k: m[k] for k in ["open", "high", "low", "close", "volume"]}, index=idx)
    df["i"] = np.arange(len(df))
    g = df.resample(tf, label="left", closed="left")
    b = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                      "close": g["close"].last(), "volume": g["volume"].sum(),
                      "i0": g["i"].min(), "i1": g["i"].max() + 1}).dropna()
    b[["i0", "i1"]] = b[["i0", "i1"]].astype(np.int64)
    return b


def _first_hit(i0, i1, d, stop, tgt, open_px):
    m = minutes()
    lo, hi, op = m["low"][i0:i1], m["high"][i0:i1], m["open"][i0:i1]
    n = i1 - i0
    hs = (lo <= stop) if d > 0 else (hi >= stop)
    if np.isnan(tgt):
        hl = np.zeros(n, bool)
    else:
        hl = (hi >= tgt) if d > 0 else (lo <= tgt)
    a = hs | hl
    if not a.any():
        return None
    k = int(np.argmax(a))
    ref = open_px if k == 0 else op[k]
    if hs[k]:  # stop first on same-minute ambiguity
        return (min(stop, ref) if d > 0 else max(stop, ref)), "SL"
    return (max(tgt, ref) if d > 0 else min(tgt, ref)), "TP"


def run(b, sig, stop, tgt=None, dyn=None, hold=10 ** 9, cost=0.0015, start=None, end=None,
        reverse=False, capital=1.0, frac=1.0, trail=None):
    """cost: per side fraction of notional (commission + slippage). frac: notional / equity."""
    n = len(b)
    o, c = b.open.values, b.close.values
    i0, i1 = b.i0.values, b.i1.values
    t = b.index
    tgt = np.full(n, np.nan) if tgt is None else np.asarray(tgt, float)
    dyn = np.full(n, np.nan) if dyn is None else np.asarray(dyn, float)
    trail = None if trail is None else np.asarray(trail, float)
    ok = np.ones(n, bool)
    if start is not None:
        ok &= t >= pd.Timestamp(start, tz="UTC")
    if end is not None:
        ok &= t < pd.Timestamp(end, tz="UTC")
    last = np.where(ok)[0].max()
    sig = np.where(ok, sig, 0)
    eq = capital
    pos = 0; qty = 0.0; ent = np.nan; ent_i = 0; st = np.nan; tp_fix = np.nan
    pend = 0
    ext = np.nan
    trades = []
    curve = np.full(n, np.nan)

    def close(px, i, why):
        nonlocal eq, pos, qty
        eq += pos * qty * (px - ent) - cost * qty * px
        trades.append((t[ent_i], t[i], pos, ent, px, pos * (px / ent - 1) - 2 * cost, why))
        pos = 0; qty = 0.0

    for i in range(n):
        if not ok[i] and pos == 0 and pend == 0:
            continue
        if pend != 0:
            d, sp, tf = pend
            if pos != 0 and pos != d:
                close(o[i], i, "rev")
            if pos == 0:
                pos = d; ent = o[i]; ent_i = i; st = sp; tp_fix = tf
                qty = eq * frac / ent
                eq -= cost * qty * ent
                ext = ent
            pend = 0
        if pos != 0 and i - ent_i >= hold:
            close(o[i], i, "time")
        if pos != 0 and trail is not None and i > ent_i:
            # chandelier: extreme close since entry -/+ k*ATR, levels from the previous close
            ext = max(ext, c[i - 1]) if pos > 0 else min(ext, c[i - 1])
            ts = ext - trail[i - 1] if pos > 0 else ext + trail[i - 1]
            st = max(st, ts) if pos > 0 else min(st, ts)
        if pos != 0:
            tg = tp_fix
            dv = dyn[i - 1] if i > 0 else np.nan
            if not np.isnan(dv):
                tg = dv if np.isnan(tg) else (min(tg, dv) if pos > 0 else max(tg, dv))
            # a target already behind the open fills at the open (limit order semantics)
            r = _first_hit(i0[i], i1[i], pos, st, tg, o[i])
            if r is not None:
                close(r[0], i, r[1])
        curve[i] = eq + (pos * qty * (c[i] - ent) if pos else 0.0)
        if i >= last:
            if pos != 0:
                close(c[i], i, "end")
                curve[i] = eq
            break
        s = sig[i]
        if s != 0 and (pos == 0 or (reverse and s != pos)):
            pend = (int(s), stop[i], tgt[i])
    tr = pd.DataFrame(trades, columns=["t_in", "t_out", "dir", "entry", "exit", "ret", "why"])
    cv = pd.Series(curve, index=t).dropna()
    return tr, cv


def stats(tr, cv):
    if len(cv) < 2:
        return {}
    yrs = max((cv.index[-1] - cv.index[0]).days / 365.25, 1e-9)
    fin = cv.iloc[-1] / cv.iloc[0]
    d = cv.resample("1D").last().dropna().pct_change().dropna()
    r = tr.ret
    gw, gl = r[r > 0].sum(), -r[r < 0].sum()
    return dict(n=len(tr), win=(r > 0).mean() if len(r) else np.nan, pf=gw / gl if gl > 0 else np.nan,
                avg=r.mean() if len(r) else np.nan,
                t=r.mean() / r.std(ddof=1) * np.sqrt(len(r)) if len(r) > 2 and r.std() > 0 else np.nan,
                net=fin - 1, cagr=fin ** (1 / yrs) - 1 if fin > 0 else -1,
                dd=(cv / cv.cummax() - 1).min(), sharpe=d.mean() / d.std() * np.sqrt(365) if d.std() > 0 else np.nan,
                expo=((tr.t_out - tr.t_in).dt.total_seconds().sum() / (yrs * 365.25 * 86400)) if len(tr) else 0)
