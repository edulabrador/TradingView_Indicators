import sys, glob, os; sys.path.insert(0,'.'); sys.path.insert(0,'..')
import port as P, pandas as pd, numpy as np, pickle
FX={}
for f in sorted(glob.glob('ext/historical-data/*/*h4.csv')):
    s=os.path.basename(f)[:-6]; d=pd.read_csv(f,parse_dates=['Date']).dropna()
    idx=pd.DatetimeIndex(d.Date).tz_localize('UTC')
    FX[s]=dict(idx=idx,o=d.open.values,h=d.high.values,l=d.low.values,c=d.close.values,start=int(np.searchsorted(idx,idx[0]+pd.Timedelta(days=90))))
print({k:(str(v['idx'][0].date()),str(v['idx'][-1].date()),len(v['c'])) for k,v in FX.items()})
P.COST=0.0002
U={s:P.unit_returns(x) for s,x in FX.items()}
R=pd.concat({s:u[0] for s,u in U.items()},axis=1); Pos=pd.concat({s:u[1] for s,u in U.items()},axis=1); Al=pd.concat({s:u[2] for s,u in U.items()},axis=1)
def vol(xs,lb=30):
    return pd.concat({s:pd.Series(x['c'],x['idx']).pct_change().rolling(lb*6,min_periods=lb*3).std()*np.sqrt(P.BPY) for s,x in xs.items()},axis=1)
V=vol(FX)
rfx,gfx=P.combine(R,Pos,Al,'risk',V,target=0.5,cap=2.0)
print('--- frozen rules on FX + gold (cost 0.02%/side), 2013-2022: per instrument Sharpe (unit, 1x)')
print({s:round(P.stats(R[s].fillna(0))['sharpe'],2) for s in R})
s=P.stats(rfx); print('FX+gold risk parity portfolio 2013-2022: Sharpe %.2f±%.2f CAGR %+.1f%% DD %.0f%%'%(s['sharpe'],s['se'],100*s['cagr'],100*s['dd']))
pickle.dump((rfx,gfx),open('data/fx_sleeve.pkl','wb'))
# overlap with crypto trend sleeve
P.COST=0.0015
C=pickle.load(open('data/unit_84_4.0_50.pkl','rb')); rc,gc=P.combine(*C,'risk',P.asset_vol(30),target=0.5,cap=2.0)
w0,w1='2017-12-01','2022-03-01'
def st(r): return P.stats(r,w0,w1)
X=pd.concat({'crypto':rc,'fx':rfx},axis=1).fillna(0)[w0:w1]
d=(1+X).groupby(X.index.floor('1D')).prod()-1; print('daily corr crypto-trend vs fx-trend: %.2f'%d.corr().iloc[0,1])
v=X.rolling(90*6,min_periods=30*6).std().shift(1); w=(1/v).div((1/v).sum(axis=1),axis=0).fillna(0.5)
mix=(w*X).sum(axis=1)
for nm,r in [('crypto trend only',rc),('fx+gold trend only',rfx),('crypto + fx trend, equal risk',mix)]:
    s=st(r); print('%-32s 2017-12..2022-03 Sharpe %.2f  CAGR %+.0f%%  vol %.0f%%  DD %.0f%%'%(nm,s['sharpe'],100*s['cagr'],100*s['vol'],100*s['dd']))
