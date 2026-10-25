import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eng, strat, pickle, pandas as pd, numpy as np
from multiprocessing import Pool
pd.set_option('display.width',250); pd.set_option('display.float_format','{:.3f}'.format)
P='data/bars_full.pkl'; B=pickle.load(open(P,'rb'))
for tf in ['30min','2h']:
    if tf not in B: B[tf]=eng.bars(tf)
pickle.dump(B,open(P,'wb'))
strat.BPD['30min']=48
CFG=dict(period=84,flat=True,side='both',trend_days=50,stop_atr=1.0,exit='R5',rej=0.6,volz=1.5)
DEV=('2018-08-01','2023-01-01')
def run(tf,cfg,win,sig=None):
    s=strat.build(B[tf],tf,**cfg)
    if sig is not None:
        s['sig']=sig
        c=B[tf].close.values; a=strat.atr(B[tf]).values; h=B[tf].high.values; l=B[tf].low.values
        s['stop']=np.where(sig>0,l-cfg['stop_atr']*a,h+cfg['stop_atr']*a); r=np.abs(c-s['stop']); m=float(cfg['exit'][1:])
        s['tgt']=np.where(sig>0,c+m*r,c-m*r)
    tr,cv=eng.run(B[tf],s['sig'],s['stop'],s['tgt'],s['dyn'],s['hold'],start=win[0],end=win[1],trail=s['trail'])
    return tr,cv
def eligible(tf,cfg):
    b=B[tf]; c=b.close; sma=c.rolling(cfg['trend_days']*strat.BPD[tf]).mean()
    return (c>sma).values,(c<sma).values
def rnd(args):
    tf,seed,win=args; rng=np.random.default_rng(seed)
    s=strat.build(B[tf],tf,**CFG); t=B[tf].index; ok=(t>=pd.Timestamp(win[0],tz='UTC'))&(t<pd.Timestamp(win[1],tz='UTC'))
    up,dn=eligible(tf,CFG); nl=((s['sig']>0)&ok).sum(); ns=((s['sig']<0)&ok).sum()
    sig=np.zeros(len(t),int)
    sig[rng.choice(np.where(up&ok)[0],nl,replace=False)]=1
    sig[rng.choice(np.where(dn&ok)[0],ns,replace=False)]=-1
    tr,cv=run(tf,CFG,win,sig); st=eng.stats(tr,cv); return tf,st['avg'],st['cagr']
if __name__=='__main__':
    rows=[]
    for tf in ['30min','1h','2h','4h']:
        tr,cv=run(tf,CFG,DEV); st=eng.stats(tr,cv); st['tf']=tf; rows.append(st)
    real=pd.DataFrame(rows).set_index('tf'); print(real)
    with Pool(4) as p: R=pd.DataFrame(p.map(rnd,[(tf,s,DEV) for tf in ['30min','1h','2h','4h'] for s in range(200)]),columns=['tf','avg','cagr'])
    for tf,g in R.groupby('tf'):
        print(tf,'random avg median',round(g.avg.median(),4),'p(avg>=real)',round((g.avg>=real.loc[tf,'avg']).mean(),3),'p(cagr>=real)',round((g.cagr>=real.loc[tf,'cagr']).mean(),3))
