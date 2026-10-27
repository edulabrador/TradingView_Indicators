import sys; sys.path.insert(0,'.'); sys.path.insert(0,'..'); sys.path.insert(0,'../sharpe'); sys.path.insert(0,'../dukascopy')
import harness as H, pickle
V=[('R2a I1 + I2 (10% threshold + continuous mom)',dict(mint=0.10,mom_mode='cont')),
   ('R2b I1 + I3 (10% threshold + breakout ensemble)',dict(mint=0.10,periods=(42,84,168))),
   ('R2c I1 + I2 + I3',dict(mint=0.10,mom_mode='cont',periods=(42,84,168))),
   ('R2d I1 + I2, threshold 20%',dict(mint=0.20,mom_mode='cont'))]
res=[H.evaluate(l,c)[0] for l,c in V]; pickle.dump(res,open('data/iter2.pkl','wb'))
