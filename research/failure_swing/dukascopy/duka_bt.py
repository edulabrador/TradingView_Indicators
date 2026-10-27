import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..'); sys.path.insert(0,'../sharpe')
import numpy as np, pandas as pd, pickle, bt, fast, pine_replica as PR
X=pickle.load(open('data/duka4h.pkl','rb'))
COST={'BTCUSD':0.0015,'XAUUSD':0.0003}
START='2022-05-01'
def bh(x):
    return fast.metrics(pd.Series(x['c'][x['start']:],x['idx'][x['start']:]).resample('1D').last().dropna())
def f(m): return 'Sharpe %5.2f  CAGR %+6.1f%%  DD %6.1f%%'%(m['sharpe'],100*m['cagr'],100*m['dd'])
print(f'=== Dukascopy backtests, {START} -> end of data, 4h bars')
for s,x in X.items():
    print(f'--- {s} (cost {COST[s]*100:.2f}%/side)   buy & hold: {f(bh(x))}')
    # 1. original Failure Swing (v3 logic and v6 port), engine of the first analysis, 1-minute intrabar
    bt.DATA=f'data/DUKA_{s}.npz'; bt._M=None; b=bt.bars('4h')
    for mode,side in [('v3',False),('v6',True)]:
        ind=bt.indicators(b,ema_side=side,start=START); tr,eq=bt.run(ind,mode=mode,commission=COST[s]*100)
        st=bt.stats(tr,eq,start=START); print('  Failure Swing %s:      trades %3d  PF %.2f  CAGR %+6.1f%%  DD %6.1f%%'%(mode,st['trades'],st['pf'],100*st['cagr'],100*st['maxdd']))
    # 2. S/R breakout, frozen (long+short, trail 4 ATR, SMA 50d)
    sig=fast.signals(x['o'],x['h'],x['l'],x['c']); a=fast.atr(x['h'],x['l'],x['c'])
    r,cv=fast.run(x['o'],x['h'],x['l'],x['c'],sig,a,cost=COST[s],start=x['start']); m=fast.metrics(fast.daily(cv,x['idx']))
    print('  S/R Breakout:         trades %3d  %s'%(len(r),f(m)))
    # 3. Breakout Momentum Vol-Target (Pine replica)
    e=PR.run(x,cost=COST[s]); m=fast.metrics(e); print('  Breakout Mom VolTgt:              %s'%f(m))
    y=e.resample('YE').last(); y0=np.r_[e.iloc[0],y.values]; print('     by year:','  '.join(f'{d.year}:{v:+.0%}' for d,v in zip(y.index,y0[1:]/y0[:-1]-1)))
    if s=='XAUUSD':
        e2=PR.run(x,cost=0.0015); print('  Breakout Mom VolTgt at 0.15%%/side: %s'%f(fast.metrics(e2)))
    pickle.dump(e,open(f'data/duka_pine_{s}.pkl','wb'))
E={s:pickle.load(open(f'data/duka_pine_{s}.pkl','rb')) for s in X}
R=pd.concat({s:e.pct_change() for s,e in E.items()},axis=1).dropna(how='all')
d=R.dropna(); print('daily corr BTC vs XAU strategy returns: %.2f'%d.corr().iloc[0,1])
p=R.mean(axis=1).dropna(); eq=(1+p).cumprod(); print('BTC + XAU equal weight (daily rebalance): %s'%f(fast.metrics(eq)))
pickle.dump(p,open('data/duka_port.pkl','wb'))
