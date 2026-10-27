import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..')
import port as P, pandas as pd, numpy as np, pickle
from it6 import voltarget, blend
I=pickle.load(open('data/it7.pkl','rb')); J=pickle.load(open('data/it8.pkl','rb'))
V6S=voltarget(blend({'bo':I['TL'],'ts':I['TSL']}),cap=1.0)
pickle.dump(V6S,open('data/v6s.pkl','wb'))
res={}
for nm,r in [('V6 spot (cap 1x)',V6S),('A',pickle.load(open('data/it4.pkl','rb'))['A']),('vol-targeted basket',J['LB'])]:
    d=(1+r).groupby(r.index.floor('1D')).prod()-1; d=d[d.ne(0).idxmax():]; res[nm]=d
    y=(1+d).groupby(d.index.year).prod()-1
    print('%-22s'%nm,'  '.join(f'{k}:{v:+.0%}' for k,v in y.items()))
d=res['V6 spot (cap 1x)']; eq=(1+d).cumprod(); uw=(eq<eq.cummax()); runs=uw.groupby((~uw).cumsum()).sum()
print('V6 spot: longest time under water %d days; exposure avg gross see below'%runs.max())
rng=np.random.default_rng(11); r=d.values; n=len(r)
for H,lab in [(365,'12m'),(5*365,'5y')]:
    sh=[];ret=[];dd=[]
    for _ in range(10000):
        idx=[]
        while len(idx)<H:
            s=rng.integers(0,n); idx.extend(range(s,min(s+rng.geometric(1/30),n)))
        p=r[np.array(idx[:H])]; e=np.cumprod(1+p); sh.append(p.mean()/p.std()*np.sqrt(365)); ret.append(e[-1]**(365/H)-1); dd.append((e/np.maximum.accumulate(e)-1).min())
    sh,ret,dd=map(np.array,(sh,ret,dd))
    print(f'MC {lab}: Sharpe p5 {np.percentile(sh,5):.2f} p50 {np.median(sh):.2f} | annual ret p5 {np.percentile(ret,5):+.0%} p50 {np.median(ret):+.0%} | DD p1 {np.percentile(dd,1):.0%} p5 {np.percentile(dd,5):.0%} p50 {np.median(dd):.0%} | P(ret<0) {(ret<0).mean():.0%}')
