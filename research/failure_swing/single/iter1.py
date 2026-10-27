import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..'); sys.path.insert(0,'../sharpe'); sys.path.insert(0,'../dukascopy')
import harness as H, pickle
V=[('I1 resize threshold 10% (fewer trades)',dict(mint=0.10)),
   ('I2 momentum continuous (vol-normalised)',dict(mom_mode='cont')),
   ('I3 breakout ensemble 42/84/168 bars',dict(periods=(42,84,168))),
   ('I4 daily bars (period 14d, same logic)',dict(daily=True,periods=(14,))),
   ('I5 no trend SMA on breakout',dict(trend_days=0))]
res=[H.evaluate(l,c)[0] for l,c in V]; pickle.dump(res,open('data/iter1.pkl','wb'))
