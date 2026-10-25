import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..')
import port as P, pandas as pd, numpy as np, pickle
I=pickle.load(open('data/it2.pkl','rb')); trend=I['r1']
C=P.frame(lambda a: pd.Series(P.A[a]['c'],P.A[a]['idx'])); Al=P.frame(lambda a: pd.Series(np.arange(len(P.A[a]['c']))>=P.A[a]['start'],P.A[a]['idx'])).fillna(False)
V=P.asset_vol(30); ret=C.pct_change()
def sleeve(Wraw,reb=42):
    """Wraw: target signed weights decided at bar close; held with weekly (42-bar) rebalance; costs on turnover and drift."""
    keep=pd.Series(np.arange(len(Wraw))%reb==0,Wraw.index)
    W=Wraw.where(keep,np.nan).ffill().fillna(0); Wl=W.shift(1).fillna(0)
    r=(Wl*ret.fillna(0)).sum(axis=1)-P.COST*(Wl-Wl.shift(1).fillna(0)).abs().sum(axis=1)-P.COST*(Wl.abs()*ret.fillna(0).abs()).sum(axis=1)
    return r
# (a) cross-sectional momentum: 30-day return rank, long top 3 / short bottom 3, inverse-vol weights, weekly
mom=C.pct_change(30*6).where(Al)
rk=mom.rank(axis=1); n=Al.sum(axis=1)
top=rk.ge((n-2).values[:,None]); bot=rk.le(3)
iv=(0.5/V).where(Al)
Wx=(iv.where(top,0)-iv.where(bot,0)).div(6)
xs=sleeve(Wx.where(n>=6,0)); P.show('(a) cross-sectional momentum, market neutral',xs)
# (b) long basket, inverse-vol, weekly
Wb=iv.div(n.replace(0,np.nan),axis=0); lb=sleeve(Wb); P.show('(b) long basket, inverse vol',lb)
for nm,x in [('trend',trend),('xs',xs),('long',lb)]: pass
D=pd.concat({'trend':trend,'xs':xs,'long':lb},axis=1); d=(1+D).groupby(D.index.floor('1D')).prod()-1
print('daily correlations:\n',d['2018':].corr().round(2))
def riskpar(cols,lb_days=90):
    """Equal risk across sleeves, weights from trailing 90-day sleeve vol, known in advance."""
    x=D[cols]; v=x.rolling(lb_days*6,min_periods=30*6).std().shift(1)
    w=(1/v).div((1/v).sum(axis=1),axis=0).fillna(0)
    return (w*x).sum(axis=1)
P.show('trend + xs (equal risk)',riskpar(['trend','xs']))
P.show('trend + long (equal risk)',riskpar(['trend','long']))
r3=riskpar(['trend','xs','long']); P.show('trend + xs + long (equal risk)',r3)
def voltarget(r,tv=0.25,lb_days=30,cap=3):
    v=r.rolling(lb_days*6,min_periods=10*6).std().shift(1)*np.sqrt(P.BPY); s=(tv/v).clip(upper=cap).fillna(0)
    return s*r-P.COST*0.0*s
for nm,r in [('trend',trend),('trend+xs',riskpar(['trend','xs'])),('trend+xs+long',r3)]:
    P.show(f'{nm}, portfolio vol target 25%',voltarget(r))
pickle.dump(dict(D=D),open('data/it3.pkl','wb'))
