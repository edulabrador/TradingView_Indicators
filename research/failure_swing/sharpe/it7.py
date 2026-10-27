import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..')
import port as P, pandas as pd, numpy as np, pickle, os
from it6 import weight_sleeve, voltarget, blend, C, V30, AlB, N
def units(p=84,k=4.0,t=50,side='both'):
    f=f'data/unit_{p}_{k}_{t}_{side}.pkl'
    if os.path.exists(f): return pickle.load(open(f,'rb'))
    U={a:P.unit_returns(P.A[a],p,k,t,side) for a in P.UNIV}; out=tuple(pd.concat({a:u[j] for a,u in U.items()},axis=1) for j in range(3)); pickle.dump(out,open(f,'wb')); return out
print('--- iteration 7: long only, computed exactly')
RL=units(side='long'); TL=P.combine(*RL,'risk',V30,target=0.5,cap=2.0)
P.show('V5 A long-only',voltarget(TL))
sigL=(sum(np.sign(C/C.shift(L*6)-1) for L in [7,30,90])/3).clip(lower=0)
TSL=weight_sleeve((sigL*(0.5/V30)).where(AlB).div(N,axis=0))
P.show('    TSMOM long-only alone',voltarget(TSL))
P.show('V6 breakout long + TSMOM long, equal risk',voltarget(blend({'bo':TL,'ts':TSL})))
pickle.dump(dict(TL=TL,TSL=TSL),open('data/it7.pkl','wb'))
