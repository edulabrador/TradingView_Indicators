"""Bar-level engine for the S/R breakout (stop-only exits, so no intrabar ambiguity: a stop is hit when the
bar's low/high crosses it and fills at the stop or at the open on a gap). Same rules as eng.run + strat.breakout,
plus execution-noise options for Monte Carlo."""
import numpy as np
import pandas as pd

BPD = {"1h": 24, "2h": 12, "4h": 6, "1D": 1}


def atr(h, l, c, n=14):
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    return pd.Series(tr).ewm(alpha=1 / n, adjust=False).mean().values


def signals(o, h, l, c, period=84, trend_bars=300, side="both"):
    res = pd.Series(h).shift(1).rolling(period).max().values
    sup = pd.Series(l).shift(1).rolling(period).min().values
    lg = c > res
    sh = c < sup
    if trend_bars > 0:
        sma = pd.Series(c).rolling(trend_bars).mean().values
        lg &= c > sma
        sh &= c < sma
    if side == "long":
        sh[:] = False
    return np.where(lg, 1, np.where(sh, -1, 0))


def run(o, h, l, c, sig, a, k=4.0, cost=0.0015, start=0, end=None, delay=0, slip=None, skip=None):
    """delay: extra bars between signal and fill. slip: per-trade extra cost array (fraction per side) or None.
    skip: boolean array, True = this signal bar's order is not executed. Returns (trade returns, equity per bar)."""
    n = len(c)
    end = n if end is None else end
    eq = 1.0
    pos = 0; qty = 0.0; ent = 0.0; ent_i = 0; st = np.nan; ext = np.nan
    pend = None
    rets = []
    curve = np.full(n, np.nan)
    ntr = 0

    def fee(j):
        return cost + (slip[j % len(slip)] if slip is not None else 0.0)

    for i in range(start, end):
        if pend is not None and i >= pend[2]:
            d, sp, _ = pend
            if pos != 0 and pos != d:
                f = fee(ntr)
                px = o[i]
                eq += pos * qty * (px - ent) - f * qty * px
                rets.append(pos * (px / ent - 1) - 2 * f); ntr += 1
                pos = 0
            if pos == 0:
                pos = d; ent = o[i]; ent_i = i; st = sp; ext = ent
                qty = eq / ent
                eq -= fee(ntr) * qty * ent
            pend = None
        if pos != 0:
            if i > ent_i:
                ext = max(ext, c[i - 1]) if pos > 0 else min(ext, c[i - 1])
                ts = ext - k * a[i - 1] if pos > 0 else ext + k * a[i - 1]
                st = max(st, ts) if pos > 0 else min(st, ts)
            hit = l[i] <= st if pos > 0 else h[i] >= st
            if hit:
                px = min(st, o[i]) if pos > 0 else max(st, o[i])
                f = fee(ntr)
                eq += pos * qty * (px - ent) - f * qty * px
                rets.append(pos * (px / ent - 1) - 2 * f); ntr += 1
                pos = 0
        curve[i] = eq + (pos * qty * (c[i] - ent) if pos else 0.0)
        if i == end - 1:
            if pos != 0:
                f = fee(ntr)
                eq += pos * qty * (c[i] - ent) - f * qty * c[i]
                rets.append(pos * (c[i] / ent - 1) - 2 * f); curve[i] = eq
            break
        s = sig[i]
        if s != 0 and (skip is None or not skip[i]) and (pos == 0 or s != pos) and pend is None:
            sp = c[i] - k * a[i] if s > 0 else c[i] + k * a[i]
            pend = (int(s), sp, i + 1 + delay)
    return np.array(rets), curve


def daily(curve, idx):
    s = pd.Series(curve, index=idx).dropna()
    return s.resample("1D").last().dropna()


def metrics(eqd):
    eqd = eqd / eqd.iloc[0]
    y = max((eqd.index[-1] - eqd.index[0]).days / 365.25, 1e-9)
    r = eqd.pct_change().dropna()
    return dict(cagr=eqd.iloc[-1] ** (1 / y) - 1 if eqd.iloc[-1] > 0 else -1.0,
                dd=(eqd / eqd.cummax() - 1).min(),
                sharpe=r.mean() / r.std() * np.sqrt(365) if r.std() > 0 else np.nan)
