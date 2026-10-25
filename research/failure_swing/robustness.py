import sys; sys.path.insert(0,'.')
import bt, pandas as pd, pickle, numpy as np, itertools
from multiprocessing import Pool
pd.set_option('display.width',220); pd.set_option('display.float_format','{:.3f}'.format)
B=pickle.load(open(bt.os.path.join(bt.os.path.dirname(bt.DATA), 'bars.pkl'),'rb'))
TFS=['30min','1h','2h','4h','6h','12h','1D']

def comm():
    rows=[]
    for tf in TFS:
        ind=bt.indicators(B[tf])
        for cm in [0,0.05,0.1,0.2]:
            tr,eq=bt.run(ind,commission=cm); s=bt.stats(tr,eq); s.update(tf=tf,comm=cm); rows.append(s)
    return pd.DataFrame(rows)[['tf','comm','trades','win','pf','avg_tr','cagr','maxdd']]

def rnd(args):
    tf,seed=args; rng=np.random.default_rng(seed)
    ind=bt.indicators(B[tf]); nl,ns=ind['long'].sum(),ind['short'].sum()
    elig=np.where((ind['vol']>0.05)&(ind['t']>=pd.Timestamp('2018-08-01',tz='UTC')))[0]
    L=np.zeros(len(ind['o']),bool); S_=L.copy()
    pick=rng.choice(elig,nl+ns,replace=False); L[pick[:nl]]=True; S_[pick[nl:]]=True
    tr,eq=bt.run(ind,random_signals=(L,S_)); s=bt.stats(tr,eq)
    return tf,s['pf'],s['cagr'],s['avg_tr']

GRID=list(itertools.product([24,42,84,168],[50,120,200],[0,2,5,8],[1,2,3,5]))
def grid(args):
    tf,(p,e,th,sl)=args; out=dict(tf=tf,period=p,ema=e,thr=th,sl=sl)
    for name,st,en in [('is','2018-08-01','2023-01-01'),('oos','2023-01-01',None),('all','2018-08-01',None)]:
        ind=bt.indicators(B[tf],period=p,ema_len=e,threshold=th,sl_pct=sl,start=st,end=en)
        tr,eq=bt.run(ind)
        if en: eq=eq[eq.index<pd.Timestamp(en,tz='UTC')]
        s=bt.stats(tr,eq,start=st); out.update({f'{name}_{k}':s[k] for k in ['trades','pf','cagr','maxdd']})
    return out

if __name__=='__main__':
    c=comm(); print(c.to_string(index=False)); c.to_csv('res_comm.csv',index=False)
    with Pool(8) as P:
        r=pd.DataFrame(P.map(rnd,[(tf,s) for tf in ['1h','4h','1D'] for s in range(100)]),columns=['tf','pf','cagr','avg_tr'])
        r.to_csv('res_random.csv',index=False)
        print(r.groupby('tf').describe(percentiles=[.05,.5,.95]).T.to_string())
        g=pd.DataFrame(P.map(grid,[(tf,x) for tf in ['1h','4h','1D'] for x in GRID]))
    g.to_csv('res_grid.csv',index=False)
