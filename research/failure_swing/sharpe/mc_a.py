import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..')
import port as P, pandas as pd, numpy as np, pickle
A=pickle.load(open('data/it4.pkl','rb'))['A']
d=((1+A).groupby(A.index.floor('1D')).prod()-1); d=d[d.ne(0).idxmax():]
print('A history', d.index[0].date(), d.index[-1].date(), 'Sharpe %.2f'%(d.mean()/d.std()*np.sqrt(365)))
rng=np.random.default_rng(7); r=d.values; n=len(r); H=365; sh=[];ret=[];dd=[]
for _ in range(20000):
    idx=[]
    while len(idx)<H:
        s=rng.integers(0,n); idx.extend(range(s,min(s+rng.geometric(1/30),n)))
    p=r[np.array(idx[:H])]; eq=np.cumprod(1+p)
    sh.append(p.mean()/p.std()*np.sqrt(365)); ret.append(eq[-1]-1); dd.append((eq/np.maximum.accumulate(eq)-1).min())
sh,ret,dd=map(np.array,(sh,ret,dd))
print('12-month paths: Sharpe p5 %.2f p25 %.2f p50 %.2f | return p5 %+.0f%% p50 %+.0f%% | maxDD p1 %.0f%% p5 %.0f%% p50 %.0f%% | P(ret<0) %.0f%%'%(
 *np.percentile(sh,[5,25,50]),100*np.percentile(ret,5),100*np.median(ret),*(100*np.percentile(dd,[1,5,50])),100*(ret<0).mean()))
