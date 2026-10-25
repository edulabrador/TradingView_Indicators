import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eng, strat, pickle, itertools, pandas as pd, numpy as np
from multiprocessing import Pool
B=pickle.load(open('data/bars_full.pkl','rb')); strat.BPD['30min']=48
WIN={'dev':('2018-08-01','2023-01-01')}
GRID=list(itertools.product(['1h','2h','4h','1D'],['long','both'],[24,42,84,168,240],[2,3,4,5],[0,50]))
def one(p):
    tf,side,per,k,td=p
    s=strat.breakout(B[tf],tf,period=per,side=side,trail_k=k,trend_days=td)
    out=dict(tf=tf,side=side,period=per,k=k,trend=td)
    for w,(a,e) in WIN.items():
        tr,cv=eng.run(B[tf],s['sig'],s['stop'],None,None,s['hold'],start=a,end=e,trail=s['trail'],reverse=True)
        out.update({f'{w}_{x}':v for x,v in eng.stats(tr,cv).items()})
    return out
if __name__=='__main__':
    with Pool(4) as P: r=pd.DataFrame(P.map(one,GRID,chunksize=4))
    r.to_csv('bo_grid.csv',index=False)
    pd.set_option('display.width',250); pd.set_option('display.float_format','{:.3f}'.format)
    print('combos',len(r),'dev cagr>0',(r.dev_cagr>0).mean(),'dev t>2',(r.dev_t>2).mean())
    for col in ['tf','side','period','k','trend']: print(r.groupby(col)[['dev_n','dev_t','dev_pf','dev_cagr','dev_sharpe','dev_dd']].median())
    print(r.pivot_table(index=['tf','period'],columns='k',values='dev_sharpe',aggfunc='median').round(2))
