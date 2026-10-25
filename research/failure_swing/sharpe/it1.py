import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..')
import port as P, pandas as pd, numpy as np, pickle
U={a:P.unit_returns(P.A[a]) for a in P.UNIV}
R=pd.concat({a:u[0] for a,u in U.items()},axis=1); Pos=pd.concat({a:u[1] for a,u in U.items()},axis=1); Al=pd.concat({a:u[2] for a,u in U.items()},axis=1)
pickle.dump((R,Pos,Al),open('data/unit_frozen.pkl','wb'))
# validation: single asset BTC unit returns vs compounding engine (Sharpe should be close to 0.91)
x=R['BTC']; print('BTC unit-return Sharpe', round(P.stats(x)['sharpe'],3), '(compounding engine 0.912)')
V=P.asset_vol(30)
print('--- iteration 1: sizing')
P.show('equal capital (baseline)', P.combine(R,Pos,Al,'equal')[0])
for cap in [1.0,2.0]:
    r,e=P.combine(R,Pos,Al,'risk',V,target=0.5,cap=cap); P.show(f'risk parity, 30d vol, cap {cap}x', r, 'avg gross %.2f'%e.mean())
