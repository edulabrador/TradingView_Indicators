import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import final, eng, strat, pandas as pd, numpy as np
from multiprocessing import Pool
B=final.B; TF=final.TF; CFG=final.CFG
WINS={'dev':('2018-08-01','2023-01-01'),'val':('2023-01-01','2025-01-01'),'hold_old':('2014-01-01','2018-01-01'),'hold_new':('2025-01-01','2026-10-26')}
b=B[TF]; c=b.close; sma=c.rolling(50*6).mean(); UP=(c>sma).values; DN=(c<sma).values; T=b.index
REAL={w:final.ev(TF,CFG,a,e)[0] for w,(a,e) in WINS.items()}
def rnd(args):
    w,seed=args; a,e=WINS[w]; rng=np.random.default_rng(seed)
    ok=(T>=pd.Timestamp(a,tz='UTC'))&(T<pd.Timestamp(e,tz='UTC')); tr=REAL[w]
    sig=np.zeros(len(T),int)
    sig[rng.choice(np.where(UP&ok)[0],(tr.dir>0).sum(),replace=False)]=1
    sig[rng.choice(np.where(DN&ok)[0],(tr.dir<0).sum(),replace=False)]=-1
    t2,cv=final.ev(TF,CFG,a,e,sig=sig); st=eng.stats(t2,cv); return w,seed,st['cagr'],st['sharpe'],t2.ret.sum()
if __name__=='__main__':
    with Pool(4) as P: R=pd.DataFrame(P.map(rnd,[(w,s) for w in WINS for s in range(300)]),columns=['win','seed','cagr','sharpe','sumret'])
    R.to_csv('final_random.csv',index=False)
    oos=['val','hold_old','hold_new']
    for w in WINS:
        tr,cv=final.ev(TF,CFG,*WINS[w]); st=eng.stats(tr,cv); g=R[R.win==w]
        print(w,'real sharpe %.2f  random median %.2f  p=%.3f'%(st['sharpe'],g.sharpe.median(),(g.sharpe>=st['sharpe']).mean()))
    # combined OOS: sum of trade returns vs random (same seed index across windows)
    real_sum=sum(REAL[w].ret.sum() for w in oos)
    comb=R[R.win.isin(oos)].groupby('seed').sumret.sum()
    print('combined OOS sum of trade returns real %.3f, random median %.3f, p=%.4f'%(real_sum,comb.median(),(comb>=real_sum).mean()))
    allo=pd.concat([REAL[w] for w in oos]); r=allo.ret
    print('combined OOS trades',len(r),'mean %.4f t %.2f'%(r.mean(),r.mean()/r.std()*np.sqrt(len(r))),'win',round((r>0).mean(),3))
    # is hold_new consistent with the earlier trade distribution?
    prior=pd.concat([REAL['dev'],REAL['val'],REAL['hold_old']]).ret.values; rng=np.random.default_rng(1); k=len(REAL['hold_new'])
    bs=np.array([rng.choice(prior,k).mean() for _ in range(20000)])
    print('hold_new mean %.4f; P(bootstrap mean of %d prior trades <= that) = %.3f'%(REAL['hold_new'].ret.mean(),k,(bs<=REAL['hold_new'].ret.mean()).mean()))
    for w in WINS:
        x=REAL[w]; print(w,'long n',(x.dir>0).sum(),'mean %.4f'%x.ret[x.dir>0].mean(),'short n',(x.dir<0).sum(),'mean %.4f'%x.ret[x.dir<0].mean())
