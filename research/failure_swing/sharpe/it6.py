import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..')
import port as P, fast, pandas as pd, numpy as np, pickle
R,Pos,Al=pickle.load(open('data/unit_84_4.0_50.pkl','rb'))
C=P.frame(lambda a: pd.Series(P.A[a]['c'],P.A[a]['idx'])); ret=C.pct_change().fillna(0); AlB=Al.fillna(False)
V30=P.asset_vol(30); N=AlB.sum(axis=1).replace(0,np.nan)
def daily_steps(W,reb=6):
    return W.where(pd.Series(np.arange(len(W))%reb==0,W.index),np.nan).ffill().fillna(0)
def weight_sleeve(Wt,reb=6):
    W=daily_steps(Wt,reb); Wl=W.shift(1).fillna(0)
    r=(Wl*ret).sum(axis=1)-P.COST*(Wl-Wl.shift(1).fillna(0)).abs().sum(axis=1)-P.COST*(Wl.abs()*ret.abs()).sum(axis=1)
    return r,Wl.abs().sum(axis=1)
def voltarget(rg,tv=0.25,lb=30,cap=3.0,reb=6):
    r,g=rg; v=r.rolling(lb*6,min_periods=60).std().shift(1)*np.sqrt(P.BPY)
    s=daily_steps((tv/v).clip(upper=cap).fillna(0),reb)
    return s*r-P.COST*(s-s.shift(1).fillna(0)).abs()*g.shift(1).fillna(0)
def blend(parts,lb=90):
    X=pd.concat({k:v[0] for k,v in parts.items()},axis=1); G=pd.concat({k:v[1] for k,v in parts.items()},axis=1)
    v=X.rolling(lb*6,min_periods=180).std().shift(1); w=daily_steps((1/v).div((1/v).sum(axis=1),axis=0).fillna(0))
    return (w*X).sum(axis=1),(w*G).sum(axis=1)
T=P.combine(R,Pos,Al,'risk',V30,target=0.5,cap=2.0)
print('--- reference'); P.show('A (it4)',voltarget(T))
# V1 TSMOM sleeve
sig=sum(np.sign(C/C.shift(L*6)-1) for L in [7,30,90])/3
TS=weight_sleeve((sig*(0.5/V30)).where(AlB).div(N,axis=0))
P.show('V1a TSMOM 7/30/90d alone, vol target',voltarget(TS))
d=pd.concat({'bo':T[0],'ts':TS[0]},axis=1); dd=(1+d).groupby(d.index.floor('1D')).prod()-1; print('    corr breakout vs TSMOM daily %.2f'%dd.corr().iloc[0,1])
P.show('V1b breakout + TSMOM equal risk, vol target',voltarget(blend({'bo':T,'ts':TS})))
# V2 long-only / short-only contribution
for side,m in [('long only',Pos.clip(lower=0)),('short only',Pos.clip(upper=0))]:
    mask=(Pos.shift(1).fillna(0)*np.sign(m.shift(1).fillna(0))>0)|(m.shift(1).fillna(0)!=0)
    Rs=R.where((Pos.shift(1).fillna(0)!=0)&(np.sign(Pos.shift(1).fillna(0))==np.sign(m.shift(1).fillna(0)+1e-12*(1 if side=='long only' else -1))),0)
    P.show(f'V2 {side} (approx: bars held on that side)',voltarget(P.combine(Rs,m,Al,'risk',V30,target=0.5,cap=2.0)))
# V3 weekly resizing
Tw=P.combine(R,Pos,Al,'risk',V30,target=0.5,cap=2.0,rebalance_bars=42)
P.show('V3 A with weekly resizing (asset + portfolio)',voltarget(Tw,reb=42))
pickle.dump(dict(T=T,TS=TS),open('data/it6.pkl','wb'))
