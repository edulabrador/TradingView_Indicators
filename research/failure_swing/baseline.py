import sys; sys.path.insert(0,'.')
import bt, pandas as pd, pickle, time
pd.set_option('display.width',200); pd.set_option('display.float_format','{:.3f}'.format)
B={}
for tf in ['15min','30min','1h','2h','4h','6h','12h','1D']:
    B[tf]=bt.bars(tf)
pickle.dump(B,open(bt.os.path.join(bt.os.path.dirname(bt.DATA), 'bars.pkl'),'wb'))
rows=[]
for tf,b in B.items():
    bh=b.close[b.index>='2018-08-01']; 
    for mode,ema_side,intr in [('v3',False,'-'),('v6',False,'minute'),('v6',True,'minute'),('v6',True,'ohlc')]:
        ind=bt.indicators(b,ema_side=ema_side)
        tr,eq=bt.run(ind,mode=mode,intrabar=intr if intr!='-' else 'minute')
        s=bt.stats(tr,eq); s.update(tf=tf,mode=mode,emaside=ema_side,intrabar=intr,bh=bh.iloc[-1]/bh.iloc[0]-1)
        rows.append(s)
df=pd.DataFrame(rows)[['tf','mode','emaside','intrabar','trades','win','pf','avg_tr','net','cagr','maxdd','bh']]
print(df.to_string(index=False)); df.to_csv('res_baseline.csv',index=False)
