import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..'); sys.path.insert(0,'../sharpe')
import numpy as np, pandas as pd, pickle, itertools, fast, assets, pine_replica as PR
from multiprocessing import Pool
from statistics import NormalDist
X=pickle.load(open('data/duka4h.pkl','rb')); COST={'BTCUSD':0.0015,'XAUUSD':0.0003}; SLIP={'BTCUSD':0.003,'XAUUSD':0.0005}
def sh(e):
    r=e.pct_change().dropna(); return r.mean()/r.std()*np.sqrt(365)
def f(m): return 'Sharpe %5.2f  CAGR %+6.1f%%  DD %6.1f%%'%(m['sharpe'],100*m['cagr'],100*m['dd'])
def port(es):
    R=pd.concat({k:e.pct_change() for k,e in es.items()},axis=1); return (1+R.mean(axis=1).dropna()).cumprod()
BASE={s:PR.run(x,cost=COST[s]) for s,x in X.items()}
# 1 data-source consistency
def section1():
    print('=== 1. SAME STRATEGY, SAME WINDOW, THREE DATA SOURCES (BTC)')
    A=assets.load_all(); w0=BASE['BTCUSD'].index[0]; w1=BASE['BTCUSD'].index[-1]
    for nm,x in [('Dukascopy',X['BTCUSD']),('Binance',A['BTC']),('Bitstamp',A['BTC_BS'])]:
        y=dict(x); i0=int(np.searchsorted(x['idx'],w0-pd.Timedelta(days=120))); i1=int(np.searchsorted(x['idx'],w1))+1
        y={k:(v[i0:i1] if k!='start' else 0) for k,v in x.items()}; y['start']=int(np.searchsorted(y['idx'],w0))
        print('  %-10s %s'%(nm,f(fast.metrics(PR.run(y,cost=0.0015)))))
# 2 block bootstrap
def section2(rng=np.random.default_rng(5)):
    print('=== 2. MONTE CARLO, block bootstrap (30-day blocks), 10,000 paths')
    for nm,e in [('BTC',BASE['BTCUSD']),('XAU',BASE['XAUUSD']),('BTC+XAU',port(BASE))]:
        r=e.pct_change().dropna().values; n=len(r)
        for H,lab in [(365,'12m'),(3*365,'3y')]:
            S_=[];R_=[];D_=[]
            for _ in range(10000):
                idx=[]
                while len(idx)<H:
                    s=rng.integers(0,n); idx.extend(range(s,min(s+rng.geometric(1/30),n)))
                p=r[np.array(idx[:H])]; q=np.cumprod(1+p); S_.append(p.mean()/p.std()*np.sqrt(365)); R_.append(q[-1]**(365/H)-1); D_.append((q/np.maximum.accumulate(q)-1).min())
            S_,R_,D_=map(np.array,(S_,R_,D_))
            print('  %-8s %s: Sharpe p5 %5.2f p50 %.2f | annual ret p5 %+4.0f%% p50 %+4.0f%% | DD p5 %4.0f%% p1 %4.0f%% | P(loss) %2.0f%%'%(nm,lab,np.percentile(S_,5),np.median(S_),100*np.percentile(R_,5),100*np.median(R_),100*np.percentile(D_,5),100*np.percentile(D_,1),100*(R_<0).mean()))
# 3 parameter MC
def _param(seed):
    rng=np.random.default_rng(seed); scale=rng.uniform(0.5,2.0)
    p=dict(period=int(rng.integers(30,201)),k=float(rng.uniform(2.5,5.5)),trend_days=int(rng.integers(20,121)),
           moms=tuple(max(1,int(round(m*scale))) for m in (7,30,90)),vol_days=int(rng.integers(15,91)))
    es={s:PR.run(x,cost=COST[s],**p) for s,x in X.items()}
    return sh(es['BTCUSD']),sh(es['XAUUSD']),sh(port(es))
def section3():
    with Pool(4) as P: R=np.array(P.map(_param,range(300)))
    print('=== 3. PARAMETER MONTE CARLO (300 random: period 30-200, trail 2.5-5.5 ATR, SMA 20-120d, momentum horizons x0.5-2, vol 15-90d)')
    for j,nm in enumerate(['BTC','XAU','BTC+XAU']):
        b=sh(BASE['BTCUSD']) if j==0 else sh(BASE['XAUUSD']) if j==1 else sh(port(BASE))
        print('  %-8s frozen %.2f | random configs Sharpe p5 %.2f p50 %.2f p95 %.2f | Sharpe>0 in %.0f%%'%(nm,b,*np.percentile(R[:,j],[5,50,95]),100*(R[:,j]>0).mean()))
# 4 execution MC
def _exec(seed):
    rng=np.random.default_rng(seed); d=int(rng.integers(0,2))
    es={s:PR.run(x,cost=COST[s],delay=d,skip=0.15,slip_max=SLIP[s],rng=rng) for s,x in X.items()}
    return d,sh(es['BTCUSD']),sh(es['XAUUSD']),sh(port(es))
def section4():
    with Pool(4) as P: R=np.array(P.map(_exec,range(200)))
    print('=== 4. EXECUTION MONTE CARLO (200 runs: 15% of orders skipped, extra slippage up to 0.3% BTC / 0.05% XAU, half the runs filled 4h late)')
    for d in [0,1]:
        s=R[R[:,0]==d]
        print('  delay %d: BTC Sharpe p5 %.2f p50 %.2f | XAU p5 %.2f p50 %.2f | BTC+XAU p5 %.2f p50 %.2f'%(d,*np.percentile(s[:,1],[5,50]),*np.percentile(s[:,2],[5,50]),*np.percentile(s[:,3],[5,50])))
# 5 synthetic
def _syn(a):
    s,seed,block=a; x=X[s]; rng=np.random.default_rng(seed); c=x['c']; pc=c[:-1]
    ro,rh,rl,rc=x['o'][1:]/pc,x['h'][1:]/pc,x['l'][1:]/pc,c[1:]/pc; n=len(rc); idx=[]
    while len(idx)<n:
        st=rng.integers(0,n); idx.extend(range(st,min(st+block,n)))
    idx=np.array(idx[:n]); cc=c[0]*np.cumprod(rc[idx]); prev=np.r_[c[0],cc[:-1]]
    y=dict(o=prev*ro[idx],h=prev*rh[idx],l=prev*rl[idx],c=cc,idx=x['idx'][1:],start=x['start'])
    return s,block,sh(PR.run(y,cost=COST[s]))
def section5():
    with Pool(4) as P: R=pd.DataFrame(P.map(_syn,[(s,i,b) for s in X for b in [1,180] for i in range(100)]),columns=['s','b','sh'])
    print('=== 5. SYNTHETIC PRICES (100 paths each): 1-bar resampling kills momentum, 30-day blocks keep it')
    for s in X:
        real=sh(BASE[s]); g1=R[(R.s==s)&(R.b==1)].sh; g2=R[(R.s==s)&(R.b==180)].sh
        print('  %s real %.2f | iid: median %.2f, P(>=real) %.2f | 30-day blocks: median %.2f, P(>=real) %.2f'%(s,real,g1.median(),(g1>=real).mean(),g2.median(),(g2>=real).mean()))
# 6 walk-forward
GR=list(itertools.product([42,84,168],[3.0,4.0,5.0],[0.5,1.0,2.0]))
def _wf(a):
    s,(p,k,m)=a; return s,(p,k,m),PR.run(X[s],period=p,k=k,moms=tuple(max(1,int(round(v*m))) for v in (7,30,90)),cost=COST[s]).pct_change().fillna(0)
def section6():
    with Pool(4) as P: R=P.map(_wf,[(s,g) for s in X for g in GR])
    print('=== 6. WALK-FORWARD (train 2 years rolling, trade next 6 months, 27 configs, pick best train Sharpe)')
    for s in X:
        D=pd.DataFrame({g:r for ss,g,r in R if ss==s}); out=[];fr=[]
        cuts=pd.date_range(D.index[0]+pd.DateOffset(years=2),D.index[-1],freq='6MS')
        for c0 in cuts:
            tr=D[(D.index>=c0-pd.DateOffset(years=2))&(D.index<c0)]; te=D[(D.index>=c0)&(D.index<c0+pd.DateOffset(months=6))]
            best=(tr.mean()/tr.std()).idxmax(); out.append(te[best]); fr.append(te[(84,4.0,1.0)])
        o=pd.concat(out); q=pd.concat(fr)
        print('  %s OOS from %s: WFO Sharpe %.2f | frozen Sharpe %.2f (same dates)'%(s,o.index[0].date(),o.mean()/o.std()*np.sqrt(365),q.mean()/q.std()*np.sqrt(365)))
# 7 PSR
def section7():
    N=NormalDist(); print('=== 7. PROBABILISTIC SHARPE (P[true Sharpe > 0]); XAU never used before -> N=1')
    for nm,e in [('BTC',BASE['BTCUSD']),('XAU',BASE['XAUUSD']),('BTC+XAU',port(BASE))]:
        r=e.pct_change().dropna(); s=r.mean()/r.std(); T=len(r); sk=r.skew(); ku=r.kurt()+3
        print('  %-8s Sharpe %.2f, %d days: PSR %.3f'%(nm,s*np.sqrt(365),T,N.cdf(s*np.sqrt(T-1)/np.sqrt(1-sk*s+(ku-1)/4*s*s))))
if __name__=='__main__':
    for fn in [section1,section2,section3,section4,section5,section6,section7]: fn(); print(flush=True)
