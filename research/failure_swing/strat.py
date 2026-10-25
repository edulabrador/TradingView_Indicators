"""Failure-swing signal family. All values computed with data up to the close of bar i."""
import numpy as np
import pandas as pd

BPD = {"1h": 24, "2h": 12, "4h": 6, "6h": 4, "12h": 2, "1D": 1}


def atr(b, n=14):
    pc = b.close.shift(1)
    tr = pd.concat([b.high - b.low, (b.high - pc).abs(), (b.low - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def build(b, tf, period=84, flat=True, side="both", trend_days=0, stop_atr=0.5, exit="R2",
          ema_len=120, vol_thr=0.0, hold=10 ** 9, rej=0.0, volz=0.0, trail_k=0.0):
    h, l, c, o = b.high, b.low, b.close, b.open
    res = h.shift(1).rolling(period).max()
    sup = l.shift(1).rolling(period).min()
    a = atr(b)
    ema = c.ewm(span=ema_len, adjust=False).mean()
    lg = (l <= sup.shift(1)) & (c > sup.shift(1))
    sh = (h >= res.shift(1)) & (c < res.shift(1))
    if flat:
        lg &= sup.shift(1) == sup.shift(2)
        sh &= res.shift(1) == res.shift(2)
    if vol_thr > 0:
        dist = (o - ema).abs() / ema
        lg &= dist > vol_thr
        sh &= dist > vol_thr
    if rej > 0:
        rng = (h - l).replace(0, np.nan)
        lg &= (c - l) / rng >= rej
        sh &= (h - c) / rng >= rej
    if volz > 0:
        lv = np.log(b.volume.replace(0, np.nan))
        z = (lv - lv.shift(1).rolling(100).mean()) / lv.shift(1).rolling(100).std()
        lg &= z >= volz
        sh &= z >= volz
    if trend_days > 0:
        sma = c.rolling(trend_days * BPD[tf]).mean()
        lg &= c > sma
        sh &= c < sma
    if side == "long":
        sh[:] = False
    elif side == "short":
        lg[:] = False
    sig = np.where(lg, 1, np.where(sh, -1, 0))
    stop = np.where(sig > 0, l - stop_atr * a, h + stop_atr * a)
    risk = np.abs(c - stop)
    tgt = np.full(len(b), np.nan)
    dyn = None
    if exit.startswith("R"):
        m = float(exit[1:])
        tgt = np.where(sig > 0, c + m * risk, c - m * risk)
    elif exit == "EMA":
        dyn = ema.values
        # entries with the EMA behind the price would exit instantly: skip them
        sig = np.where((sig > 0) & (ema.values <= c.values), 0, sig)
        sig = np.where((sig < 0) & (ema.values >= c.values), 0, sig)
    elif exit == "TRAIL":
        pass
    tr = (trail_k * a).values if trail_k > 0 else None
    return dict(sig=sig, stop=np.asarray(stop, float), tgt=tgt, dyn=dyn, hold=hold, trail=tr)


def breakout(b, tf, period=84, side="long", trail_k=3.0, trend_days=0):
    """Break of the same support/resistance levels, closing beyond them; ATR chandelier exit."""
    h, l, c = b.high, b.low, b.close
    res = h.shift(1).rolling(period).max()
    sup = l.shift(1).rolling(period).min()
    a = atr(b)
    lg = c > res
    sh = c < sup
    if trend_days > 0:
        sma = c.rolling(trend_days * BPD[tf]).mean()
        lg &= c > sma
        sh &= c < sma
    if side == "long":
        sh[:] = False
    sig = np.where(lg, 1, np.where(sh, -1, 0))
    stop = np.where(sig > 0, c - trail_k * a, c + trail_k * a)
    return dict(sig=sig, stop=np.asarray(stop, float), tgt=None, dyn=None, hold=10 ** 9,
                trail=(trail_k * a).values)
