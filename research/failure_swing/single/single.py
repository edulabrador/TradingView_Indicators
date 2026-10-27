"""Single-symbol strategy (TradingView use case) with optional improvements, bar by bar, orders at next open."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..'); sys.path.insert(0,'../sharpe'); sys.path.insert(0,'../dukascopy')
import numpy as np, pandas as pd, fast
def run(x, bpd=6, periods=(84,), k=4.0, trend_days=50, moms=(7,30,90), mom_mode="binary", vol_days=30, tv=0.40,
        maxe=1.0, mint=0.02, cost=0.0015, w_bo=0.5, vol_mode="roll", ewma_hl_days=10, gate_days=0):
    o,h,l,c,idx=x['o'],x['h'],x['l'],x['c'],x['idx']; n=len(c)
    a=fast.atr(h,l,c); sma=pd.Series(c).rolling(int(trend_days*bpd)).mean().values if trend_days else np.full(n,-np.inf)
    res=[pd.Series(h).shift(1).rolling(int(p)).max().values for p in periods]
    lr=np.r_[np.nan,np.log(c[1:]/c[:-1])]; sig_b=pd.Series(lr).rolling(int(vol_days*bpd)).std().values
    if vol_mode=="ewma":
        sig_b=np.sqrt(pd.Series(lr**2).ewm(halflife=ewma_hl_days*bpd,min_periods=int(10*bpd)).mean().values)
    vol=sig_b*np.sqrt(bpd*365)
    gate=(c>pd.Series(c).rolling(int(gate_days*bpd)).mean().values).astype(float) if gate_days else np.ones(n)
    if mom_mode=="binary":
        mom=sum((c>pd.Series(c).shift(int(m*bpd)).values).astype(float) for m in moms)/len(moms)
    else:   # volatility-normalised trend strength, clipped to [0,1]
        z=sum(np.log(c/pd.Series(c).shift(int(m*bpd)).values)/(sig_b*np.sqrt(m*bpd)) for m in moms)/len(moms)
        mom=np.clip(np.nan_to_num(z),0,1)
    day=idx.floor('1D').values; newday=np.r_[True,day[1:]!=day[:-1]]
    cash=1.0; qty=0.0; m_=len(periods); bo=np.zeros(m_,int); st=np.full(m_,np.nan); ext=np.full(m_,np.nan)
    pend=None; eq=np.full(n,np.nan)
    for i in range(x['start'],n):
        if pend is not None:
            dq=max(pend,-qty); px=o[i]; cash-=dq*px+abs(dq)*px*cost; qty+=dq; pend=None
        prev=bo.copy()
        for j in range(m_):
            if bo[j]==1:
                if l[i]<=st[j]: bo[j]=0
                else: ext[j]=max(ext[j],c[i]); st[j]=max(st[j],ext[j]-k*a[i])
            if bo[j]==0 and c[i]>res[j][i] and c[i]>sma[i]:
                bo[j]=1; ext[j]=c[i]; st[j]=c[i]-k*a[i]
        E=cash+qty*c[i]; eq[i]=E
        s=(w_bo*bo.mean()+(1-w_bo)*mom[i])*gate[i]
        ex=0.0 if (np.isnan(vol[i]) or vol[i]==0) else min(maxe,tv/vol[i])*s
        d=E*ex/c[i]-qty
        if (newday[i] or (bo!=prev).any()) and abs(d)*c[i]>mint*E: pend=d
        elif ex==0 and qty>0: pend=-qty
    return pd.Series(eq,idx).dropna().resample('1D').last().dropna()
def to_daily(x):
    """Resample a 4h dict to daily bars (for the 1D-timeframe variant)."""
    s=pd.DataFrame({'o':x['o'],'h':x['h'],'l':x['l'],'c':x['c']},index=x['idx'])
    g=s.resample('1D'); d=pd.DataFrame({'o':g.o.first(),'h':g.h.max(),'l':g.l.min(),'c':g.c.last()}).dropna()
    st=x['idx'][x['start']].floor('1D')
    return dict(idx=d.index,o=d.o.values,h=d.h.values,l=d.l.values,c=d.c.values,start=int(np.searchsorted(d.index,st)))
