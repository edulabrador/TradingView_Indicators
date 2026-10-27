import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..'); sys.path.insert(0,'../sharpe'); sys.path.insert(0,'../dukascopy')
import harness as H, single, fast, numpy as np, pandas as pd, pickle
from multiprocessing import Pool
B=dict(mint=0.10,mom_mode='cont')
_,df_b,E0=H.evaluate('baseline',{},show=False); out,df,E=H.evaluate('R2a final candidate',B)
def port(names,EE):
    R=pd.concat({n:EE[n].pct_change() for n in names},axis=1); return R.mean(axis=1,skipna=True).dropna()
def S(r,a=None,b=None):
    r=r[a:b] if (a or b) else r; return r.mean()/r.std()*np.sqrt(365)
def row(lab,r):
    eq=(1+r).cumprod(); y=(eq.index[-1]-eq.index[0]).days/365.25
    print('  %-38s Sharpe %.2f | dev %.2f | 2023-26 %.2f | 2025-26 %.2f | CAGR %+.0f%% DD %.0f%%'%(lab,S(r),S(r,None,'2022-12-31'),S(r,'2023-01-01'),S(r,'2025-01-01'),100*(eq.iloc[-1]**(1/y)-1),100*(eq/eq.cummax()-1).min()))
print('--- baskets (one TradingView chart per symbol, equal capital, rebalanced daily)')
for lab,names in [('12 Binance pairs',H.BIN),('BTC + ETH',['BTC','ETH']),('BTC + ETH + SOL',['BTC','ETH','SOL']),('top-5 by size (BTC ETH BNB SOL XRP)',['BTC','ETH','BNB','SOL','XRP'])]:
    row(lab+' baseline',port(names,E0)); row(lab+' R2a',port(names,E))
row('Dukascopy BTC + XAU baseline',port(['DK_BTC','DK_XAU'],E0)); row('Dukascopy BTC + XAU R2a',port(['DK_BTC','DK_XAU'],E))
pickle.dump((E0,E),open('data/iter4.pkl','wb'))
print('--- R2a sensitivity (one change at a time): 12-pair single-asset median full / 2023-26, BTC Binance, 12-pair basket Sharpe')
for lab,c in [('threshold 5%',dict(B,mint=0.05)),('threshold 15%',dict(B,mint=0.15)),('momentum 14/60/180',dict(B,moms=(14,60,180))),('momentum 3/14/60',dict(B,moms=(3,14,60))),
              ('breakout period 42',dict(B,periods=(42,))),('breakout period 168',dict(B,periods=(168,))),('trail 3 ATR',dict(B,k=3.0)),('trail 5 ATR',dict(B,k=5.0)),
              ('vol window 15d',dict(B,vol_days=15)),('vol window 60d',dict(B,vol_days=60)),('weight breakout 0.3',dict(B,w_bo=0.3)),('weight breakout 0.7',dict(B,w_bo=0.7)),
              ('cost 0.25%/side',dict(B,cost=0.0025))]:
    o,d,EE=H.evaluate(lab,c,show=False); r=port(H.BIN,EE)
    print('  %-22s median %.2f / %.2f | BTC %.2f | basket %.2f (2023-26 %.2f)'%(lab,o['med_full'],o['med_test'],o['btc_bin'],S(r),S(r,'2023-01-01')))
