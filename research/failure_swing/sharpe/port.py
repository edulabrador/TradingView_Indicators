"""Portfolio construction on top of the S/R breakout: unit-notional returns per 4h bar, volatility targeting,
multi-lookback ensembles, cross-sectional momentum sleeve. Costs: 0.15% per side on every notional traded,
including resizes."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np, pandas as pd
import assets, fast

try:
    A = assets.load_all()
except Exception:   # data not prepared yet; callers like portfolio_a set A themselves
    A = {}
UNIV = [a for a in assets.NAMES if a != "BTC_BS"]   # 12 Binance pairs
COST = 0.0015
BPY = 6 * 365


def unit_returns(x, period=84, k=4.0, trend_days=50, side="both"):
    """Per-bar return of a 1x-notional position following the breakout rules (stops intrabar), net of entry/exit
    costs; plus the position held at each close."""
    o, h, l, c = x["o"], x["h"], x["l"], x["c"]
    sig = fast.signals(o, h, l, c, period, int(trend_days * 6), side)
    a = fast.atr(h, l, c)
    n = len(c); r = np.zeros(n); posv = np.zeros(n)
    pos = 0; st = ext = np.nan; ent_i = 0; pend = None
    for i in range(x["start"], n):
        ref = c[i - 1]
        if pend is not None:
            d, sp = pend
            if pos != 0 and pos != d:
                r[i] += pos * (o[i] / ref - 1) - COST; pos = 0
            if pos == 0:
                pos = d; st = sp; ext = o[i]; ent_i = i; r[i] -= COST; ref = o[i]
            pend = None
        if pos != 0:
            if i > ent_i:
                ext = max(ext, c[i - 1]) if pos > 0 else min(ext, c[i - 1])
                ts = ext - k * a[i - 1] if pos > 0 else ext + k * a[i - 1]
                st = max(st, ts) if pos > 0 else min(st, ts)
            if (l[i] <= st) if pos > 0 else (h[i] >= st):
                px = min(st, o[i]) if pos > 0 else max(st, o[i])
                r[i] += pos * (px / ref - 1) - COST; pos = 0
            else:
                r[i] += pos * (c[i] / ref - 1)
        posv[i] = pos
        s = sig[i]
        if s != 0 and s != pos:
            pend = (int(s), c[i] - k * a[i] if s > 0 else c[i] + k * a[i])
    idx = x["idx"]
    alive = np.zeros(n, bool); alive[x["start"]:] = True
    return pd.Series(r, idx), pd.Series(posv, idx), pd.Series(alive, idx)


def frame(fn):
    """Apply fn(asset) -> Series on a common 4h index for the universe."""
    return pd.concat({a: fn(a) for a in UNIV}, axis=1).sort_index()


def asset_vol(lookback_days=30):
    """Ex-ante annualised volatility of each asset from 4h close-to-close returns, known at each close."""
    def f(a):
        x = A[a]; rr = pd.Series(x["c"], x["idx"]).pct_change()
        return rr.rolling(lookback_days * 6, min_periods=lookback_days * 3).std() * np.sqrt(BPY)
    return frame(f)


def combine(R, P, alive, scheme="equal", vol=None, target=0.20, rebalance_bars=6, cap=2.0):
    """R, P: unit returns / positions (bars x assets). Weights fixed at the close before each bar.
    scheme 'equal': capital / N_alive per asset. 'risk': (target / vol) / N_alive, rescaled at most every rebalance_bars.
    Returns portfolio bar returns (net of resize costs) and gross exposure."""
    alive = alive.fillna(False)
    N = alive.sum(axis=1).replace(0, np.nan)
    if scheme == "equal":
        W = alive.div(N, axis=0)
    else:
        raw = (target / vol).clip(upper=cap * 3).where(alive)
        W = raw.div(N, axis=0)
        # only update weights every rebalance_bars bars (step function)
        keep = np.arange(len(W)) % rebalance_bars == 0
        W = W.where(pd.Series(keep, W.index), np.nan).ffill()
        g = W.sum(axis=1)
        W = W.div(np.maximum(g / cap, 1.0), axis=0)        # gross notional cap
    W = W.fillna(0)
    Wl = W.shift(1).fillna(0)                                # weight in force during bar t
    port = (Wl * R.fillna(0)).sum(axis=1)
    held = P.shift(1).fillna(0).abs()                        # position open coming into bar t
    resize = (Wl - Wl.shift(1).fillna(0)).abs() * held
    port -= COST * resize.sum(axis=1)
    # constant-notional sleeves are re-trimmed every bar: charge the drift (|bar return| of the notional held)
    port -= COST * (Wl * P.shift(1).fillna(0).abs() * R.fillna(0).abs()).sum(axis=1)
    expo = (Wl * P.shift(1).fillna(0).abs()).sum(axis=1)
    return port, expo


def stats(r, start=None, end=None):
    r = r[start:end] if (start or end) else r
    r = r[r.index >= r.ne(0).idxmax()]
    d = (1 + r).groupby(r.index.floor("1D")).prod() - 1
    eq = (1 + d).cumprod(); y = (d.index[-1] - d.index[0]).days / 365.25
    sh = d.mean() / d.std() * np.sqrt(365)
    return dict(sharpe=sh, cagr=eq.iloc[-1] ** (1 / y) - 1, vol=d.std() * np.sqrt(365), dd=(eq / eq.cummax() - 1).min(),
                se=np.sqrt((1 + 0.5 * sh ** 2) / y))


def show(name, r, extra=""):
    full, dev, test = stats(r), stats(r, None, "2022-12-31"), stats(r, "2023-01-01")
    print("%-44s full Sh %.2f±%.2f CAGR %+5.0f%% vol %3.0f%% DD %4.0f%% | dev Sh %.2f | 2023-26 Sh %.2f | 2025-26 Sh %.2f %s" % (
        name, full["sharpe"], full["se"], 100 * full["cagr"], 100 * full["vol"], 100 * full["dd"], dev["sharpe"], test["sharpe"],
        stats(r, "2025-01-01")["sharpe"], extra))
    return full
