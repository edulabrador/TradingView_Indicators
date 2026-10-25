import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eng, strat, pickle, itertools, pandas as pd, numpy as np
from multiprocessing import Pool
B=pickle.load(open('data/bars_full.pkl','rb'))
DEV=('2018-08-01','2023-01-01')
GRID=list(itertools.product(['1h','4h','1D'],['long','both'],[50,200],[24,84],[0,0.6],[0,1.5],[('R3',0),('R5',0),('NONE',3),('NONE',5)]))
def one(p):
    tf,side,td,per,rej,vz,(ex,tk)=p
    s=strat.build(B[tf],tf,period=per,flat=True,side=side,trend_days=td,stop_atr=1.0,exit=ex,rej=rej,volz=vz,trail_k=tk)
    tr,cv=eng.run(B[tf],s['sig'],s['stop'],s['tgt'],s['dyn'],s['hold'],start=DEV[0],end=DEV[1],trail=s['trail'])
    st=eng.stats(tr,cv); st.update(tf=tf,side=side,trend=td,period=per,rej=rej,volz=vz,exit=ex,trail=tk); return st
if __name__=='__main__':
    with Pool(4) as P: r=pd.DataFrame(P.map(one,GRID,chunksize=4))
    r.to_csv('dev_grid2.csv',index=False); print(len(r))
