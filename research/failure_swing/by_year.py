import sys; sys.path.insert(0,'.')
import bt, pandas as pd, pickle, numpy as np
pd.set_option('display.width',220); pd.set_option('display.float_format','{:.3f}'.format)
B=pickle.load(open(bt.os.path.join(bt.os.path.dirname(bt.DATA), 'bars.pkl'),'rb'))
for tf in ['1h','4h']:
    ind=bt.indicators(B[tf]); tr,eq=bt.run(ind)
    tr['r']=tr.dir*(tr.exit/tr.entry-1)-0.004; tr['y']=tr.t_in.dt.year
    print('==',tf); print(tr.pivot_table(index='y',columns='dir',values='r',aggfunc=['count','sum']).round(3))
    ye=eq.resample('YE').last(); print((ye/ye.shift(1).fillna(1000)-1).round(3).to_string())
    m=tr.r; t=m.mean()/m.std()*np.sqrt(len(m)); print('mean net/trade',round(m.mean(),4),'t-stat',round(t,2))
    for d in [1,-1]:
        x=tr.r[tr.dir==d]; print('dir',d,'n',len(x),'mean',round(x.mean(),4),'t',round(x.mean()/x.std()*np.sqrt(len(x)),2))
    tr2,eq2=bt.run(ind,allow_short=False); s=bt.stats(tr2,eq2); print('long-only',{k:round(v,3) for k,v in s.items()})
