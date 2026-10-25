import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..')
import port as P, pandas as pd, numpy as np, pickle, os
def units(period=84,k=4.0,trend_days=50):
    f=f'data/unit_{period}_{k}_{trend_days}.pkl'
    if os.path.exists(f): return pickle.load(open(f,'rb'))
    U={a:P.unit_returns(P.A[a],period,k,trend_days) for a in P.UNIV}
    out=tuple(pd.concat({a:u[j] for a,u in U.items()},axis=1) for j in range(3)); pickle.dump(out,open(f,'wb')); return out
V=P.asset_vol(30)
R,Pos,Al=units()
print('--- iteration 1 again, with drift cost')
P.show('equal capital, daily constant notional',P.combine(R,Pos,Al,'equal')[0])
r1,_=P.combine(R,Pos,Al,'risk',V,target=0.5,cap=2.0); P.show('risk parity (it1)',r1)
print('--- iteration 2: ensemble of lookbacks (7,14,28,56 days), k=4, SMA 50d, equal sub-weights')
E=[units(p) for p in [42,84,168,336]]
Re=sum(e[0].fillna(0) for e in E)/4; Pe=sum(e[1] for e in E)/4
r2,_=P.combine(Re,Pe,Al,'risk',V,target=0.5,cap=2.0); P.show('ensemble lookbacks, risk parity',r2)
E2=[units(84,kk) for kk in [3.0,4.0,5.0]]
Rk=sum(e[0].fillna(0) for e in E2)/3; Pk=sum(e[1] for e in E2)/3
P.show('ensemble trail k 3/4/5 (p84), risk parity',P.combine(Rk,Pk,Al,'risk',V,target=0.5,cap=2.0)[0])
E3=[units(p,kk) for p in [42,84,168,336] for kk in [3.0,5.0]]
R3=sum(e[0].fillna(0) for e in E3)/8; P3=sum(e[1] for e in E3)/8
r3,_=P.combine(R3,P3,Al,'risk',V,target=0.5,cap=2.0); P.show('ensemble 4 lookbacks x k 3/5, risk parity',r3)
pickle.dump(dict(r1=r1,r2=r2,r3=r3),open('data/it2.pkl','wb'))
print('corr it1 vs ensemble', round(r1.corr(r2),2))
