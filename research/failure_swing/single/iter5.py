import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..'); sys.path.insert(0,'../sharpe'); sys.path.insert(0,'../dukascopy')
import numpy as np, pandas as pd, pickle
E0,E=pickle.load(open('data/iter4.pkl','rb'))
def S(r,a=None,b=None):
    r=r[a:b] if (a or b) else r; return r.mean()/r.std()*np.sqrt(365)
def norebal(names,EE,start):
    eq=pd.concat({n:EE[n][EE[n].index>=start]/EE[n][EE[n].index>=start].iloc[0] for n in names},axis=1).ffill().mean(axis=1); return eq.pct_change().dropna(),eq
def monthly(names,EE):
    R=pd.concat({n:EE[n].pct_change() for n in names},axis=1).dropna(); eq=[];v=np.ones(len(names))/len(names); out=[]
    for m,g in R.groupby(R.index.to_period('M')):
        for _,row in g.iterrows():
            v=v*(1+row.values); out.append(v.sum())
        v=np.ones(len(names))*v.sum()/len(names)
    e=pd.Series(out,R.index); return e.pct_change().dropna(),e
for lab,names in [('top-5',['BTC','ETH','BNB','SOL','XRP']),('BTC+ETH+SOL',['BTC','ETH','SOL']),('BTC+ETH',['BTC','ETH'])]:
    st=max(E[n].index[0] for n in names)
    for kind,(r,eq) in [('no rebalance',norebal(names,E,st)),('monthly rebalance',monthly(names,E))]:
        y=(eq.index[-1]-eq.index[0]).days/365.25
        print('%-12s R2a %-18s from %s: Sharpe %.2f | 2023-26 %.2f | 2025-26 %.2f | CAGR %+.0f%% DD %.0f%%'%(lab,kind,st.date(),S(r),S(r,'2023-01-01'),S(r,'2025-01-01'),100*((eq.iloc[-1]/eq.iloc[0])**(1/y)-1),100*(eq/eq.cummax()-1).min()))
r,eq=monthly(['BTC','ETH','BNB','SOL','XRP'],E); pickle.dump(r,open('data/top5_monthly.pkl','wb'))
yy=(1+r).groupby(r.index.year).prod()-1; print('top-5 monthly, by year:','  '.join(f'{k}:{v:+.0%}' for k,v in yy.items()))
rng=np.random.default_rng(3); x=r.values; n=len(x)
for H,lab in [(365,'12m'),(3*365,'3y'),(5*365,'5y')]:
    S_=[];R_=[];D_=[]
    for _ in range(10000):
        idx=[]
        while len(idx)<H:
            s=rng.integers(0,n); idx.extend(range(s,min(s+rng.geometric(1/30),n)))
        p=x[np.array(idx[:H])]; q=np.cumprod(1+p); S_.append(p.mean()/p.std()*np.sqrt(365)); R_.append(q[-1]**(365/H)-1); D_.append((q/np.maximum.accumulate(q)-1).min())
    S_,R_,D_=map(np.array,(S_,R_,D_))
    print('MC top-5 %s: Sharpe p5 %.2f p50 %.2f | annual ret p5 %+.0f%% p50 %+.0f%% | DD p5 %.0f%% p1 %.0f%% | P(loss) %.0f%% | P(Sharpe>1) %.0f%%'%(lab,np.percentile(S_,5),np.median(S_),100*np.percentile(R_,5),100*np.median(R_),100*np.percentile(D_,5),100*np.percentile(D_,1),100*(R_<0).mean(),100*(S_>1).mean()))
