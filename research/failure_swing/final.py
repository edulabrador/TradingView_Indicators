import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eng, strat, pickle, itertools, pandas as pd, numpy as np
from multiprocessing import Pool
pd.set_option('display.width',250); pd.set_option('display.float_format','{:.3f}'.format)
B=pickle.load(open('data/bars_full.pkl','rb'))
CFG=dict(period=84,side='both',trail_k=4,trend_days=50); TF='4h'
WINS=[('val','2023-01-01','2025-01-01'),('hold_old','2014-01-01','2018-01-01'),('hold_new','2025-01-01','2026-10-26')]
WINS=WINS[:int(sys.argv[1])] if len(sys.argv)>1 else WINS
def ev(tf,cfg,a,e,cost=0.0015,sig=None):
    s=strat.breakout(B[tf],tf,**cfg)
    if sig is not None: s['sig']=sig; c=B[tf].close.values; at=strat.atr(B[tf]).values; s['stop']=np.where(sig>0,c-cfg['trail_k']*at,c+cfg['trail_k']*at)
    tr,cv=eng.run(B[tf],s['sig'],s['stop'],None,None,s['hold'],start=a,end=e,trail=s['trail'],reverse=True,cost=cost)
    return tr,cv
def nb(p):
    (w,a,e),per,k,side=p
    tr,cv=ev(TF,dict(period=per,side=side,trail_k=k,trend_days=50),a,e); st=eng.stats(tr,cv); return w,per,k,side,st['cagr'],st['pf']
if __name__=='__main__':
    rows=[]
    for w,a,e in WINS:
        for cost in [0.0015,0.0025]:
            tr,cv=ev(TF,CFG,a,e,cost); st=eng.stats(tr,cv); st.update(win=w,cost=cost); rows.append(st)
    print(pd.DataFrame(rows).set_index(['win','cost']))
    with Pool(4) as P: N=pd.DataFrame(P.map(nb,list(itertools.product(WINS,[42,84,168],[3,4,5],['long','both']))),columns=['win','per','k','side','cagr','pf'])
    print(N.groupby('win').apply(lambda g: pd.Series({'n':len(g),'frac_cagr>0':(g.cagr>0).mean(),'median_cagr':g.cagr.median(),'min_cagr':g.cagr.min()})))
