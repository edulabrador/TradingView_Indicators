import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eng, strat, pickle, itertools, pandas as pd, numpy as np
from multiprocessing import Pool
TFS=['1h','4h','1D']
if not os.path.exists('data/bars_full.pkl'):
    pickle.dump({tf:eng.bars(tf) for tf in TFS},open('data/bars_full.pkl','wb'))
B=pickle.load(open('data/bars_full.pkl','rb'))
DEV=('2018-08-01','2023-01-01')
GRID=list(itertools.product(TFS,['long','short','both'],[0,50,200],[24,84],[True,False],[0.25,1.0],['R1','R2','R3','EMA'],[0,5]))
def one(p):
    tf,side,td,per,flat,sa,ex,hd=p
    s=strat.build(B[tf],tf,period=per,flat=flat,side=side,trend_days=td,stop_atr=sa,exit=ex,hold=hd*strat.BPD[tf] if hd else 10**9)
    tr,cv=eng.run(B[tf],s['sig'],s['stop'],s['tgt'],s['dyn'],s['hold'],start=DEV[0],end=DEV[1])
    st=eng.stats(tr,cv); st.update(tf=tf,side=side,trend=td,period=per,flat=flat,stop_atr=sa,exit=ex,hold=hd); return st
if __name__=='__main__':
    with Pool(4) as P: r=pd.DataFrame(P.map(one,GRID,chunksize=8))
    r.to_csv('dev_grid.csv',index=False); print(len(r))
