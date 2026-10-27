import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..'); sys.path.insert(0,'../sharpe'); sys.path.insert(0,'../dukascopy')
import harness as H, pickle
B=dict(mint=0.10,mom_mode='cont')
V=[('R3a R2a + EWMA vol (half-life 10d)',dict(B,vol_mode='ewma')),
   ('R3b R2a + 200d regime gate',dict(B,gate_days=200)),
   ('R3c R2a + EWMA + 200d gate',dict(B,vol_mode='ewma',gate_days=200))]
res=[H.evaluate(l,c)[0] for l,c in V]; pickle.dump(res,open('data/iter3.pkl','wb'))
