import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..')
import port as P, pandas as pd, numpy as np, pickle
import it6
from it6 import weight_sleeve, voltarget, blend, C, AlB, N
from it7 import units
I=pickle.load(open('data/it7.pkl','rb')); TL,TSL=I['TL'],I['TSL']
def tsm(V,hs=(7,30,90)):
    s=(sum(np.sign(C/C.shift(L*6)-1) for L in hs)/len(hs)).clip(lower=0)
    return weight_sleeve((s*(0.5/V)).where(AlB).div(N,axis=0))
V30=P.asset_vol(30)
base=voltarget(blend({'bo':TL,'ts':TSL})); P.show('V6',base)
print('--- control: always-long basket, same sizing and portfolio vol target')
LB=weight_sleeve(((0.5/V30)).where(AlB).div(N,axis=0)); P.show('vol-targeted buy & hold basket',voltarget(LB))
x=pd.concat({'v6':base,'lb':voltarget(LB)},axis=1); d=(1+x).groupby(x.index.floor('1D')).prod()-1; print('    daily corr V6 vs basket %.2f'%d.corr().iloc[0,1])
print('--- sensitivity (one change at a time)')
for vlb in [15,60,90]:
    V=P.asset_vol(vlb); P.show(f'asset vol window {vlb}d',voltarget(blend({'bo':P.combine(*units(side="long"),'risk',V,target=0.5,cap=2.0),'ts':tsm(V)})))
for hs in [(14,60,180),(3,14,60),(30,)]:
    P.show(f'TSMOM horizons {hs}',voltarget(blend({'bo':TL,'ts':tsm(V30,hs)})))
for p,k,t in [(42,4.0,50),(168,4.0,50),(84,3.0,50),(84,5.0,50),(84,4.0,100),(84,4.0,0)]:
    P.show(f'breakout {p}/{k}/{t}',voltarget(blend({'bo':P.combine(*units(p,k,t,'long'),'risk',V30,target=0.5,cap=2.0),'ts':TSL})))
for lb in [15,60]:
    P.show(f'portfolio vol window {lb}d',voltarget(blend({'bo':TL,'ts':TSL}),lb=lb))
for cap in [1.0,2.0]:
    P.show(f'portfolio leverage cap {cap}x',voltarget(blend({'bo':TL,'ts':TSL}),cap=cap))
for c in [0.0005,0.0025]:
    P.COST=c; it6.P.COST=c
    TLc=P.combine(*units(side='long'),'risk',V30,target=0.5,cap=2.0); TSc=tsm(V30)
    P.show(f'cost {c*100:.2f}%/side',voltarget(blend({'bo':TLc,'ts':TSc})))
P.COST=0.0015
pickle.dump(dict(V6=base,LB=voltarget(LB)),open('data/it8.pkl','wb'))
