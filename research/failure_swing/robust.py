"""Robustness battery for the S/R breakout strategy (frozen: 4h, period 84, trail 4 ATR, SMA 50 days, long+short).
Usage: python3 robust.py [wfo|mc|params|exec|synth|dsr|all]"""
import sys, os, itertools, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from multiprocessing import Pool
from statistics import NormalDist
_N = NormalDist()
class norm:
    ppf = staticmethod(_N.inv_cdf)
    cdf = staticmethod(_N.cdf)
import assets, fast

A = assets.load_all()
ALTS = [a for a in assets.NAMES if a != "BTC_BS"]          # 12 Binance pairs (portfolio universe)
FROZEN = dict(period=84, k=4.0, trend_days=50)
OUT = {}


def strat_daily(x, period, k, trend_days, cost=0.0015, **kw):
    sig = fast.signals(x["o"], x["h"], x["l"], x["c"], period, int(trend_days * 6))
    a = fast.atr(x["h"], x["l"], x["c"])
    r, cv = fast.run(x["o"], x["h"], x["l"], x["c"], sig, a, k=k, cost=cost, start=x["start"], **kw)
    return r, fast.daily(cv, x["idx"])


def bh_daily(x):
    return pd.Series(x["c"][x["start"]:], index=x["idx"][x["start"]:]).resample("1D").last().dropna()


def portfolio(daily_eq):
    """Equal weight across the assets alive each day, rebalanced daily."""
    R = pd.concat({k: v.pct_change() for k, v in daily_eq.items()}, axis=1)
    return R.mean(axis=1, skipna=True).dropna()


def m_ret(r):
    eq = (1 + r).cumprod()
    return fast.metrics(pd.concat([pd.Series([1.0], index=[r.index[0] - pd.Timedelta(days=1)]), eq]))


def fmt(m):
    return "CAGR %+6.1f%%  DD %6.1f%%  Sharpe %5.2f" % (100 * m["cagr"], 100 * m["dd"], m["sharpe"])


# ---------------------------------------------------------------- 1. walk-forward optimisation
GRID = list(itertools.product([24, 42, 84, 168, 240], [2, 3, 4, 5, 6], [0, 30, 50, 100]))


def _grid_asset(a):
    x = A[a]
    return a, {g: strat_daily(x, *g)[1].pct_change().fillna(0) for g in GRID}


def wfo():
    with Pool(4) as P:
        G = dict(P.map(_grid_asset, assets.NAMES))
    keys = GRID
    per_k = {p: i for i, p in enumerate([24, 42, 84, 168, 240])}
    kk = {k: i for i, k in enumerate([2, 3, 4, 5, 6])}
    tt = {t: i for i, t in enumerate([0, 30, 50, 100])}

    def sharpe(r):
        return r.mean() / r.std() * np.sqrt(365) if r.std() > 0 else -9

    res, oos = {}, {"best": {}, "plateau": {}, "frozen": {}, "bh": {}}
    picks = []
    for a in assets.NAMES:
        R = pd.DataFrame(G[a])
        idx = R.index
        first = idx[0] + pd.DateOffset(years=3)
        cuts = pd.date_range(first.normalize() + pd.offsets.MonthBegin(0), idx[-1], freq="6MS")
        seg = {m: [] for m in oos}
        bh = bh_daily(A[a]).pct_change().fillna(0)
        ins = []
        for c0 in cuts:
            c1 = c0 + pd.DateOffset(months=6)
            tr = R[(R.index >= c0 - pd.DateOffset(years=3)) & (R.index < c0)]
            te = R[(R.index >= c0) & (R.index < c1)]
            if len(te) < 20:
                continue
            s = tr.apply(sharpe)
            best = s.idxmax()
            # plateau: average Sharpe of the config and its grid neighbours
            arr = np.full((5, 5, 4), np.nan)
            for g, v in s.items():
                arr[per_k[g[0]], kk[g[1]], tt[g[2]]] = v
            sm = {}
            for g in keys:
                i, j, t = per_k[g[0]], kk[g[1]], tt[g[2]]
                sm[g] = np.nanmean(arr[max(0, i - 1):i + 2, max(0, j - 1):j + 2, max(0, t - 1):t + 2])
            plat = max(sm, key=sm.get)
            seg["best"].append(te[best]); seg["plateau"].append(te[plat])
            seg["frozen"].append(te[(84, 4, 50)]); seg["bh"].append(bh[(bh.index >= c0) & (bh.index < c1)])
            ins.append(s[plat]); picks.append((a, str(c0.date()), plat))
        for m in oos:
            oos[m][a] = pd.concat(seg[m])
        res[a] = {m: m_ret(oos[m][a]) for m in oos}
        res[a]["is_sharpe_plateau"] = float(np.mean(ins))
        res[a]["start"] = str(oos["best"][a].index[0].date())
    print("=== 1. WALK-FORWARD (train 3 years rolling, trade next 6 months, grid of 100 configs)")
    print("%-7s %-10s | %-40s | %-40s | %-40s | %s" % ("asset", "OOS from", "WFO best-Sharpe pick", "WFO plateau pick", "frozen config", "buy & hold"))
    for a in assets.NAMES:
        r = res[a]
        print("%-7s %-10s | %s | %s | %s | %s" % (a, r["start"], fmt(r["best"]), fmt(r["plateau"]), fmt(r["frozen"]), fmt(r["bh"])))
    print("portfolio of the 12 Binance pairs (equal weight, daily rebalance), OOS segments only:")
    for m in oos:
        pr = pd.concat({a: oos[m][a] for a in ALTS}, axis=1).mean(axis=1, skipna=True).dropna()
        mm = m_ret(pr); OUT[f"wfo_port_{m}"] = mm
        print("  %-8s %s" % (m, fmt(mm)))
        y = (1 + pr).groupby(pr.index.year).prod() - 1
        print("           by year:", "  ".join(f"{k}:{v:+.0%}" for k, v in y.items()))
    eff = [res[a]["plateau"]["sharpe"] / res[a]["is_sharpe_plateau"] for a in assets.NAMES if res[a]["is_sharpe_plateau"] > 0]
    print("walk-forward efficiency (OOS Sharpe / IS Sharpe, plateau pick): median %.2f" % np.median(eff))
    pk = pd.DataFrame(picks, columns=["asset", "from", "cfg"])
    print("most chosen plateau configs:", pk.cfg.value_counts().head(5).to_dict())
    OUT["wfo"] = {a: {m: res[a][m] for m in oos} for a in assets.NAMES}


# ---------------------------------------------------------------- 2. Monte Carlo of returns
def frozen_port():
    D = {a: strat_daily(A[a], **FROZEN)[1] for a in ALTS}
    return portfolio(D), {a: strat_daily(A[a], **FROZEN)[0] for a in ["BTC_BS"]}


def mc():
    port, tr = frozen_port()
    bh = portfolio({a: bh_daily(A[a]) for a in ALTS})
    rng = np.random.default_rng(42)
    print("=== 2. MONTE CARLO")
    print("historical portfolio (frozen, 12 pairs, daily rebalance) %s .. %s: %s" % (port.index[0].date(), port.index[-1].date(), fmt(m_ret(port))))
    print("buy & hold same basket:                                   %s" % fmt(m_ret(bh)))
    # (a) stationary block bootstrap of daily portfolio returns, 5-year paths
    r = port.values; n = len(r); H = 5 * 365; B = 10000; L = 30
    cagr, dd, neg1, neg2, uw = [], [], [], [], []
    for _ in range(B):
        idx = []
        while len(idx) < H:
            s = rng.integers(0, n); idx.extend(range(s, min(s + rng.geometric(1 / L), n)))
        p = r[np.array(idx[:H])]
        eq = np.cumprod(1 + p); peak = np.maximum.accumulate(eq)
        cagr.append(eq[-1] ** (1 / 5) - 1); dd.append((eq / peak - 1).min())
        yr = np.prod((1 + p[:365 * 5].reshape(5, 365)), axis=1) - 1
        neg1.append((yr < 0).mean()); neg2.append(np.any((yr[:-1] < 0) & (yr[1:] < 0)))
        under = eq < peak; longest = 0; cur = 0
        for u in under:
            cur = cur + 1 if u else 0; longest = max(longest, cur)
        uw.append(longest)
    cagr, dd, uw = np.array(cagr), np.array(dd), np.array(uw)
    q = lambda v: "p5 %+.0f%% | p50 %+.0f%% | p95 %+.0f%%" % tuple(100 * np.percentile(v, [5, 50, 95]))
    print("(a) block bootstrap (mean block 30 days), %d paths of 5 years:" % B)
    print("    CAGR      ", q(cagr)); print("    max DD    ", q(dd))
    print("    P(5-year CAGR < 0) = %.1f%%   P(max DD worse than -50%%) = %.1f%%   P(DD worse than -70%%) = %.1f%%" % (100 * (cagr < 0).mean(), 100 * (dd < -0.5).mean(), 100 * (dd < -0.7).mean()))
    print("    share of losing calendar years: %.0f%%   P(at least 2 losing years in a row within 5 years) = %.0f%%" % (100 * np.mean(neg1), 100 * np.mean(neg2)))
    print("    longest time under water: p50 %d days, p95 %d days" % tuple(np.percentile(uw, [50, 95])))
    OUT["mc_block"] = dict(cagr=np.percentile(cagr, [5, 50, 95]).tolist(), dd=np.percentile(dd, [5, 50, 95]).tolist(),
                           p_loss=float((cagr < 0).mean()), p_2neg=float(np.mean(neg2)))
    # (b) BTC trade sequence: reshuffle order (drawdown risk) and bootstrap (outcome uncertainty)
    t = tr["BTC_BS"]; nt = len(t)
    dds, fin = [], []
    for _ in range(B):
        p = rng.permutation(t); eq = np.cumprod(1 + p); dds.append((eq / np.maximum.accumulate(eq) - 1).min())
        bsp = rng.choice(t, nt); fin.append(np.prod(1 + bsp))
    dds, fin = np.array(dds), np.array(fin)
    eq = np.cumprod(1 + t); real_dd = (eq / np.maximum.accumulate(eq) - 1).min()
    print("(b) BTC 2014-2026, %d trades. Trade-order reshuffle: max DD p50 %.0f%%, p95 %.0f%% (historical %.0f%%)" % (nt, 100 * np.median(dds), 100 * np.percentile(dds, 5), 100 * real_dd))
    print("    trade bootstrap: P(total result < 0 over %d trades) = %.2f%%; median multiple x%.0f" % (nt, 100 * (fin < 1).mean(), np.median(fin)))
    st, cur, worst = 0, 0, 0
    for v in t:
        cur = cur + 1 if v < 0 else 0; worst = max(worst, cur)
    sims = []
    for _ in range(2000):
        p = rng.permutation(t); c2 = w2 = 0
        for v in p:
            c2 = c2 + 1 if v < 0 else 0; w2 = max(w2, c2)
        sims.append(w2)
    print("    longest losing streak: historical %d trades; reshuffled p50 %d, p95 %d" % (worst, np.median(sims), np.percentile(sims, 95)))


# ---------------------------------------------------------------- 3. parameter Monte Carlo
def _param(seed):
    rng = np.random.default_rng(seed)
    g = dict(period=int(rng.integers(30, 201)), k=float(rng.uniform(2.5, 5.5)), trend_days=float(rng.uniform(20, 120)))
    port = portfolio({a: strat_daily(A[a], **g)[1] for a in ALTS})
    btc = strat_daily(A["BTC_BS"], **g)[1]
    return g, m_ret(port), fast.metrics(btc)


def params():
    with Pool(4) as P:
        R = P.map(_param, range(300))
    bh = m_ret(portfolio({a: bh_daily(A[a]) for a in ALTS}))
    pc = np.array([r[1]["cagr"] for r in R]); ps = np.array([r[1]["sharpe"] for r in R]); pd_ = np.array([r[1]["dd"] for r in R])
    bc = np.array([r[2]["cagr"] for r in R]); bs = np.array([r[2]["sharpe"] for r in R])
    print("=== 3. PARAMETER MONTE CARLO (300 random configs: period 30-200, trail 2.5-5.5 ATR, SMA 20-120 days)")
    print("12-pair portfolio: CAGR>0 in %.0f%%; Sharpe p5 %.2f | p50 %.2f | p95 %.2f; DD p50 %.0f%%; Sharpe > buy&hold (%.2f) in %.0f%%" % (
        100 * (pc > 0).mean(), *np.percentile(ps, [5, 50, 95]), 100 * np.median(pd_), bh["sharpe"], 100 * (ps > bh["sharpe"]).mean()))
    print("BTC 2014-2026:     CAGR>0 in %.0f%%; Sharpe p5 %.2f | p50 %.2f | p95 %.2f" % (100 * (bc > 0).mean(), *np.percentile(bs, [5, 50, 95])))
    worst = sorted(R, key=lambda r: r[1]["sharpe"])[:3]
    print("worst portfolio configs:", [(r[0]["period"], round(r[0]["k"], 1), round(r[0]["trend_days"]), round(r[1]["sharpe"], 2)) for r in worst])
    OUT["params"] = dict(port_cagr_pos=float((pc > 0).mean()), port_sharpe=np.percentile(ps, [5, 50, 95]).tolist())


# ---------------------------------------------------------------- 4. execution Monte Carlo
def _exec(seed):
    rng = np.random.default_rng(seed)
    delay = int(rng.integers(0, 2)); skipp = 0.15; slipmax = 0.003
    D = {}
    for a in ALTS + ["BTC_BS"]:
        x = A[a]
        skip = rng.random(len(x["c"])) < skipp
        slip = rng.uniform(0, slipmax, 2000)
        D[a] = strat_daily(x, **FROZEN, delay=delay, skip=skip, slip=slip)[1]
    btc = D.pop("BTC_BS")
    return delay, m_ret(portfolio(D)), fast.metrics(btc)


def execmc():
    with Pool(4) as P:
        R = P.map(_exec, range(200))
    print("=== 4. EXECUTION MONTE CARLO (200 runs: 15% of signals missed, extra slippage U(0, 0.3%) per side, 50% of runs filled 4h late)")
    for d in [0, 1]:
        s = [r for r in R if r[0] == d]
        ps = np.array([r[1]["sharpe"] for r in s]); pc = np.array([r[1]["cagr"] for r in s]); bc = np.array([r[2]["cagr"] for r in s])
        print("  delay %d bar: n=%d  portfolio CAGR p5 %+.0f%% p50 %+.0f%% p95 %+.0f%%, CAGR>0 in %.0f%%, Sharpe p50 %.2f | BTC CAGR p50 %+.0f%%, >0 in %.0f%%" % (
            d, len(s), *(100 * np.percentile(pc, [5, 50, 95])), 100 * (pc > 0).mean(), np.median(ps), 100 * np.median(bc), 100 * (bc > 0).mean()))


# ---------------------------------------------------------------- 5. synthetic prices (null of no serial dependence)
def _synth(args):
    a, seed, block = args
    x = A[a]; rng = np.random.default_rng(seed)
    s0 = max(x["start"] - 400, 1)
    c = x["c"]; pc = c[s0 - 1:-1]
    ro, rh, rl, rc = x["o"][s0:] / pc, x["h"][s0:] / pc, x["l"][s0:] / pc, c[s0:] / pc
    n = len(rc); idx = []
    while len(idx) < n:
        s = rng.integers(0, n); idx.extend(range(s, min(s + block, n)))
    idx = np.array(idx[:n])
    cc = c[s0 - 1] * np.cumprod(rc[idx]); prev = np.r_[c[s0 - 1], cc[:-1]]
    y = dict(o=prev * ro[idx], h=prev * rh[idx], l=prev * rl[idx], c=cc, idx=x["idx"][s0:], start=x["start"] - s0)
    return a, block, fast.metrics(strat_daily(y, **FROZEN)[1])["sharpe"]


def synth():
    jobs = [(a, s, b) for a in ["BTC_BS", "ETH", "SOL", "XRP"] for b in [1, 180] for s in range(100)]
    with Pool(4) as P:
        R = pd.DataFrame(P.map(_synth, jobs), columns=["asset", "block", "sharpe"])
    print("=== 5. SYNTHETIC PRICES (100 paths per asset; 4h bars resampled with replacement)")
    print("  block=1 bar destroys all serial dependence (momentum); block=180 bars (30 days) keeps it")
    for a in ["BTC_BS", "ETH", "SOL", "XRP"]:
        real = fast.metrics(strat_daily(A[a], **FROZEN)[1])["sharpe"]
        g1 = R[(R.asset == a) & (R.block == 1)].sharpe; g2 = R[(R.asset == a) & (R.block == 180)].sharpe
        print("  %-7s real Sharpe %.2f | iid paths: median %.2f, P(>=real) %.2f | 30-day blocks: median %.2f, P(>=real) %.2f" % (
            a, real, g1.median(), (g1 >= real).mean(), g2.median(), (g2 >= real).mean()))


# ---------------------------------------------------------------- 6. deflated Sharpe ratio
def dsr():
    here = os.path.dirname(os.path.abspath(__file__))
    sh = []
    for f, col in [("dev_grid.csv", "sharpe"), ("dev_grid2.csv", "sharpe"), ("bo_grid.csv", "dev_sharpe")]:
        p = os.path.join(here, f)
        if os.path.exists(p):
            sh.extend(pd.read_csv(p)[col].dropna().tolist())
    sh = np.array(sh) / np.sqrt(365)            # annualised -> daily
    N = 2900; g = 0.5772156649
    Vraw = sh.var()
    Vtrue = max(Vraw - 1 / 1615, 1e-8)   # trials were measured on ~4.4 years (1615 days): remove their sampling noise
    port, _ = frozen_port()
    alts = portfolio({a: strat_daily(A[a], **FROZEN)[1] for a in ALTS if a != "BTC"})
    btc = strat_daily(A["BTC_BS"], **FROZEN)[1].pct_change().dropna()
    print("=== 6. PROBABILISTIC / DEFLATED SHARPE RATIO (Bailey & Lopez de Prado)")
    for label, V in [("raw trial variance", Vraw), ("trial variance minus sampling noise", Vtrue)]:
        sr0 = np.sqrt(V) * ((1 - g) * norm.ppf(1 - 1 / N) + g * norm.ppf(1 - 1 / (N * np.e)))
        print("  %s: expected best annual Sharpe of %d useless trials = %.2f" % (label, N, sr0 * np.sqrt(365)))
    def ps(r, sr0):
        r = r.values; T = len(r); s = r.mean() / r.std(); sk = pd.Series(r).skew(); ku = pd.Series(r).kurt() + 3
        return s * np.sqrt(365), T, norm.cdf((s - sr0) * np.sqrt(T - 1) / np.sqrt(1 - sk * s + (ku - 1) / 4 * s ** 2))
    sr0t = np.sqrt(Vtrue) * ((1 - g) * norm.ppf(1 - 1 / N) + g * norm.ppf(1 - 1 / (N * np.e)))
    for name, r, kind in [("BTC 2014-2026 (in sample)", btc, "dsr"), ("12-pair portfolio", port, "dsr"),
                          ("11 alts, frozen rules (OOS)", alts, "psr"), ("BTC 2014-17 holdout (OOS)", btc[:"2017"], "psr"),
                          ("BTC 2023-24 (OOS)", btc["2023":"2024"], "psr"), ("BTC 2025-26 holdout (OOS)", btc["2025":], "psr")]:
        sa, T, p0 = ps(r, 0.0); _, _, pd_ = ps(r, sr0t)
        print("  %-30s Sharpe %5.2f/yr, %4d days | PSR(Sharpe>0) %.3f | DSR(N=%d) %.3f" % (name, sa, T, p0, N, pd_))
    print("  OOS rows were selected by a single pre-fixed config (N=1), so PSR is the relevant figure for them.")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name, fn in [("wfo", wfo), ("mc", mc), ("params", params), ("exec", execmc), ("synth", synth), ("dsr", dsr)]:
        if what in (name, "all"):
            fn(); print(flush=True)
