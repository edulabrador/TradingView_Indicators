"""Bar-by-bar replica of 'Breakout Momentum Vol-Target Strategy v6.pine' (orders at next open, 0.15%/side)."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..')
import numpy as np, pandas as pd, fast, assets
def run(x, period=84, k=4.0, trend_days=50, moms=(7,30,90), vol_days=30, tv=0.40, maxe=1.0, mint=0.02, cost=0.0015,
        delay=0, skip=0.0, slip_max=0.0, rng=None):
    o,h,l,c,idx=x['o'],x['h'],x['l'],x['c'],x['idx']; n=len(c)
    res=pd.Series(h).shift(1).rolling(period).max().values; a=fast.atr(h,l,c)
    sma=pd.Series(c).rolling(trend_days*6).mean().values
    mom=sum((c>pd.Series(c).shift(m*6).values).astype(float) for m in moms)/len(moms)
    lr=np.r_[np.nan,np.log(c[1:]/c[:-1])]; vol=pd.Series(lr).rolling(vol_days*6).std().values*np.sqrt(6*365)
    day=idx.floor('1D').values; newday=np.r_[True,day[1:]!=day[:-1]]
    cash=1.0; qty=0.0; bo=0; st=ext=np.nan; pend=None; eq=np.full(n,np.nan)
    for i in range(x['start'],n):
        if pend is not None and i>=pend[1]:       # orders sent at a previous close fill at this open
            dq=pend[0]; px=o[i]
            if dq<0: dq=max(dq,-qty)
            c_=cost+(rng.uniform(0,slip_max) if slip_max>0 else 0.0)
            cash-=dq*px+abs(dq)*px*c_; qty+=dq; pend=None
        prev=bo
        if bo==1:
            if l[i]<=st: bo=0
            else:
                ext=max(ext,c[i]); st=max(st,ext-k*a[i])
        if bo==0 and c[i]>res[i] and (trend_days==0 or c[i]>sma[i]):
            bo=1; ext=c[i]; st=c[i]-k*a[i]
        E=cash+qty*c[i]; eq[i]=E
        sig=0.5*bo+0.5*mom[i]
        ex=0.0 if (np.isnan(vol[i]) or vol[i]==0) else min(maxe,tv/vol[i])*sig
        d=E*ex/c[i]-qty
        if pend is not None: continue
        if skip>0 and rng.random()<skip: continue
        if (newday[i] or bo!=prev) and abs(d)*c[i]>mint*E: pend=(d,i+1+delay)
        elif ex==0 and qty>0: pend=(-qty,i+1+delay)
    return pd.Series(eq,idx).dropna().resample('1D').last().dropna()
if __name__=='__main__':
    A=assets.load_all(); U=[a for a in assets.NAMES if a!='BTC_BS']
    D={a:run(A[a]) for a in U}
    rows=[]
    for a,e in D.items():
        m=fast.metrics(e); bh=fast.metrics(pd.Series(A[a]['c'][A[a]['start']:],A[a]['idx'][A[a]['start']:]).resample('1D').last().dropna())
        rows.append((a,m['sharpe'],m['cagr'],m['dd'],bh['sharpe'],bh['dd']))
    df=pd.DataFrame(rows,columns=['asset','sharpe','cagr','dd','bh_sharpe','bh_dd']); pd.set_option('display.float_format','{:.2f}'.format)
    print(df.to_string(index=False)); print('median single-asset Sharpe %.2f (B&H median %.2f)'%(df.sharpe.median(),df.bh_sharpe.median()))
    R=pd.concat({a:e.pct_change() for a,e in D.items()},axis=1).mean(axis=1).dropna()
    eqp=(1+R).cumprod(); y=(eqp.index[-1]-eqp.index[0]).days/365.25
    for lab,rr in [('full',R),('2023-26',R['2023':]),('2025-26',R['2025':])]:
        print('equal-weight portfolio of 12 Pine sleeves %s: Sharpe %.2f'%(lab,rr.mean()/rr.std()*np.sqrt(365)))
    print('  CAGR %+.0f%%  DD %.0f%%'%(100*(eqp.iloc[-1]**(1/y)-1),100*(eqp/eqp.cummax()-1).min()))
    e=D['BTC']; print('BTC Pine version: ',{k:round(v,2) for k,v in fast.metrics(e).items()})
    b=run(A['BTC_BS']); print('BTC Bitstamp 2014-26 Pine version:',{k:round(v,2) for k,v in fast.metrics(b).items()})
