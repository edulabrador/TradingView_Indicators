import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..')
import port as P, pandas as pd, numpy as np, pickle
R,Pos,Al=pickle.load(open('data/unit_84_4.0_50.pkl','rb'))
C=P.frame(lambda a: pd.Series(P.A[a]['c'],P.A[a]['idx'])); ret=C.pct_change().fillna(0)
AlB=Al.fillna(False)
def trend_sleeve(vlb=30,cost=0.0015):
    P.COST=cost; V=P.asset_vol(vlb); r,g=P.combine(R,Pos,Al,'risk',V,target=0.5,cap=2.0); P.COST=0.0015; return r,g
def long_sleeve(vlb=30,cost=0.0015,reb=42):
    V=P.asset_vol(vlb); n=AlB.sum(axis=1).replace(0,np.nan)
    W=(0.5/V).where(AlB).div(n,axis=0)
    keep=pd.Series(np.arange(len(W))%reb==0,W.index); W=W.where(keep,np.nan).ffill().fillna(0); Wl=W.shift(1).fillna(0)
    r=(Wl*ret).sum(axis=1)-cost*(Wl-Wl.shift(1).fillna(0)).abs().sum(axis=1)-cost*(Wl.abs()*ret.abs()).sum(axis=1)
    return r,Wl.abs().sum(axis=1)
def blend(parts,lb_days=90):
    X=pd.concat({k:v[0] for k,v in parts.items()},axis=1); G=pd.concat({k:v[1] for k,v in parts.items()},axis=1)
    v=X.rolling(lb_days*6,min_periods=30*6).std().shift(1); w=(1/v).div((1/v).sum(axis=1),axis=0).fillna(0)
    w=w.where(pd.Series(np.arange(len(w))%6==0,w.index),np.nan).ffill().fillna(0)
    return (w*X).sum(axis=1),(w*G).sum(axis=1)
def voltarget(rg,tv=0.25,lb_days=30,cap=3.0,cost=0.0015):
    r,g=rg; v=r.rolling(lb_days*6,min_periods=10*6).std().shift(1)*np.sqrt(P.BPY)
    s=(tv/v).clip(upper=cap).fillna(0); s=s.where(pd.Series(np.arange(len(s))%6==0,s.index),np.nan).ffill().fillna(0)
    return s*r-cost*(s-s.shift(1).fillna(0)).abs()*g.shift(1).fillna(0), s*g
T=trend_sleeve(); L=long_sleeve()
print('--- iteration 4 (all resizing costs charged)')
P.show('A  trend only, vol target 25%',voltarget(T)[0],'avg gross %.2f'%voltarget(T)[1].mean())
B=blend({'t':T,'l':L}); P.show('B  trend + long basket, vol target 25%',voltarget(B)[0],'avg gross %.2f'%voltarget(B)[1].mean())
print('--- sensitivity (each line changes one choice)')
for vlb in [15,60,90]:
    P.show(f'A asset vol lookback {vlb}d',voltarget(trend_sleeve(vlb))[0])
for lb in [15,60]:
    P.show(f'A portfolio vol lookback {lb}d',voltarget(T,lb_days=lb)[0])
for cap in [1.5,5.0]:
    P.show(f'A portfolio leverage cap {cap}',voltarget(T,cap=cap)[0])
for c in [0.0005,0.0025]:
    P.show(f'A cost {c*100:.2f}%/side',voltarget(trend_sleeve(cost=c),cost=c)[0])
    P.show(f'B cost {c*100:.2f}%/side',voltarget(blend({'t':trend_sleeve(cost=c),'l':long_sleeve(cost=c)}),cost=c)[0])
for p,k,t in [(42,4.0,50),(168,4.0,50),(84,3.0,50),(84,5.0,50),(84,4.0,100)]:
    try:
        RR=pickle.load(open(f'data/unit_{p}_{k}_{t}.pkl','rb'))
    except FileNotFoundError:
        U={a:P.unit_returns(P.A[a],p,k,t) for a in P.UNIV}; RR=tuple(pd.concat({a:u[j] for a,u in U.items()},axis=1) for j in range(3)); pickle.dump(RR,open(f'data/unit_{p}_{k}_{t}.pkl','wb'))
    r,g=P.combine(RR[0],RR[1],RR[2],'risk',P.asset_vol(30),target=0.5,cap=2.0)
    P.show(f'A with breakout params {p}/{k}/{t}',voltarget((r,g))[0])
pickle.dump(dict(A=voltarget(T)[0],B=voltarget(B)[0]),open('data/it4.pkl','wb'))
