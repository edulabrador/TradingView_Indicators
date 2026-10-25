import sys,os; sys.path.insert(0,'.')
import strat, pickle, pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.float_format','{:.2f}'.format)
B=pickle.load(open('data/bars_full.pkl','rb')); strat.BPD['30min']=48
W=('2018-08-01','2025-01-01'); K=[1,3,6,12,24,48]
rows=[]
for tf in ['30min','1h','2h','4h','1D']:
    b=B[tf]; o,h,l,c=b.open,b.high,b.low,b.close; a=strat.atr(b)
    ok=((b.index>=pd.Timestamp(W[0],tz='UTC'))&(b.index<pd.Timestamp(W[1],tz='UTC')))
    sma=c.rolling(50*strat.BPD[tf]).mean(); up=c>sma
    rng=(h-l).replace(0,np.nan)
    for per in [24,84,240]:
        res=h.shift(1).rolling(per).max(); sup=l.shift(1).rolling(per).min()
        L=(l<=sup.shift(1))&(c>sup.shift(1)); S_=(h>=res.shift(1))&(c<res.shift(1))
        # continuation counterpart: genuine break that closes beyond the level
        Lb=(l<=sup.shift(1))&(c<sup.shift(1)); Sb=(h>=res.shift(1))&(c>res.shift(1))
        for name,ev,d in [('FS long',L,1),('FS short',S_,-1),('break down',Lb,-1),('break up',Sb,1)]:
            for reg,mask in [('all',ok),('up',ok&up),('down',ok&~up)]:
                e=(ev&mask).values; 
                if e.sum()<20: continue
                r={'tf':tf,'per':per,'ev':name,'reg':reg,'n':int(e.sum())}
                for k in K:
                    fwd=(c.shift(-k)/o.shift(-1)-1)/(a/c)*d  # in ATR units, signed in event direction
                    base=fwd[mask.values if hasattr(mask,'values') else mask]
                    x=fwd[e].dropna(); bb=base.dropna()
                    r[f'k{k}']=(x.mean()-bb.mean())/np.sqrt(x.var()/len(x)+bb.var()/len(bb))
                rows.append(r)
df=pd.DataFrame(rows); df.to_csv('event.csv',index=False)
print('t-stat of mean forward return (ATR units, sign = event direction) vs all bars of same regime')
print(df[df.reg!='x'].to_string(index=False))
