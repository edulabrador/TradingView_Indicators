import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..'); sys.path.insert(0,'../sharpe'); sys.path.insert(0,'../dukascopy')
import numpy as np, pandas as pd, pickle, assets, single, pine_replica as PR
from multiprocessing import Pool
A=assets.load_all(); DK=pickle.load(open('../dukascopy/data/duka4h.pkl','rb'))
BIN=[a for a in assets.NAMES if a!='BTC_BS']
SETS={**{a:(A[a],0.0015) for a in BIN},'BTC_BS':(A['BTC_BS'],0.0015),'DK_BTC':(DK['BTCUSD'],0.0015),'DK_XAU':(DK['XAUUSD'],0.0003)}
def sh(e,a=None,b=None):
    r=e.pct_change().dropna(); r=r[a:b] if (a or b) else r
    return r.mean()/r.std()*np.sqrt(365) if len(r)>30 and r.std()>0 else np.nan
def _one(args):
    name,cfg=args; x,cost=SETS[name]; c=dict(cfg); daily=c.pop('daily',False)
    if daily: x=single.to_daily(x); c['bpd']=1
    cost=c.pop("cost",cost); e=single.run(x,cost=cost,**c)
    return name,sh(e),sh(e,None,'2022-12-31'),sh(e,'2023-01-01'),sh(e,'2025-01-01'),e
def evaluate(label,cfg,show=True):
    with Pool(4) as P: R=P.map(_one,[(n,cfg) for n in SETS])
    df=pd.DataFrame([r[:5] for r in R],columns=['set','full','dev','test','r25']).set_index('set')
    b=df.loc[BIN]
    out=dict(label=label,med_full=b.full.median(),med_dev=b.dev.median(),med_test=b.test.median(),med_25=b.r25.median(),
             n_gt1=int((b.full>1).sum()),btc_bin=df.loc['BTC','full'],btc_bs=df.loc['BTC_BS','full'],dk_btc=df.loc['DK_BTC','full'],dk_xau=df.loc['DK_XAU','full'],
             btc_test=df.loc['BTC','test'])
    E={r[0]:r[5] for r in R}
    if show:
        print('%-46s | 12 pairs median: full %.2f dev %.2f 2023-26 %.2f 2025-26 %.2f, >1 in %2d/12 | BTC Binance %.2f (2023-26 %.2f), Bitstamp %.2f, Duka BTC %.2f, Duka XAU %.2f'%(
            label,out['med_full'],out['med_dev'],out['med_test'],out['med_25'],out['n_gt1'],out['btc_bin'],out['btc_test'],out['btc_bs'],out['dk_btc'],out['dk_xau']),flush=True)
    return out,df,E
