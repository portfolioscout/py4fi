def compTrade(dt):
    d=0.001
    dt['reg']=np.where(dt['dmacd']>d,1,0)
    dt['reg']=np.where(dt['dmacd']<-d,-1,dt['reg'])
    dt['strategy']=dt['reg'].shift(1)*dt['market']
    return dt

import warnings
warnings.simplefilter('ignore')

import numpy as np
import pandas as pd



import pandas.io.data as web
import matplotlib.pyplot as plt

def getClose(h5,sym):
    for c in h5.keys():
        for i in h5[c]['Close'].columns:
            if sym == i:
                return h5[c]['Close'][i]
        
    return None

def fromYahoo(name,sdate='2015-01-01',edate='2015-12-31'):
    
    DT = web.DataReader(name, data_source='yahoo',
                 start=sdate,end=edate)    
    return DT

def macd(DT):
    

    
    DT['Date'] = pd.to_datetime( DT.index)
    tempds = DT.sort('Date',ascending = True )
    firstDate = tempds['Date'][0]
    DT['CloseN'] = DT['Close']/DT['Close'][firstDate]
    
    cs = tempds['Close']
    firstClose=tempds['Close'][firstDate]
    macd=pd.ewma(cs,span=12)-pd.ewma(cs,span=26)
    signal=pd.ewma(macd,span=9)
    
    DT['macd'] = macd
    DT['signal'] = signal
    DT['dmacd'] = macd-signal
    DT['market']=np.log(cs/cs.shift(1))
    return compTrade(DT)


def plotMacd(DT):
    fig, axs = plt.subplots(4,1,figsize=(42, 60))
    
    DT['CloseN'].plot(ax=axs[0], grid=True)
    DT['macd'].plot(ax=axs[1], grid=True)
    DT['signal'].plot(ax=axs[1], grid=True)
    DT['dmacd'].plot(ax=axs[2], grid=True)
    DT['reg'].plot(ax=axs[2], grid=True)
    DT[['market','strategy']].cumsum().apply(np.exp).plot(ax=axs[3], grid=True)
    
def doCumsum(dt):
    ntrades=0
    prev=0
    for e in dt['reg']:
        if prev !=e:
            ntrades=ntrades+1
        prev = e
        
    dcumsum = dt[['market','strategy']].cumsum()    
    dcumsum['delta']=(dcumsum['strategy']-dcumsum['market'])*100
    mean=dcumsum['delta'].mean()
    rmse = np.sqrt(((dcumsum['delta']-mean)**2).mean())
    win=np.compress(dcumsum['delta']>0.001,dcumsum['delta']).size*1.0/len(dcumsum['delta'])*100
    lpos=len(dcumsum)-1
    last=dcumsum['delta'][lpos]
    strat=np.exp(dcumsum['strategy'][lpos])
    bhold=np.exp(dcumsum['market'][lpos])

    print 'mean','rmse', 'win','ntrades','last','strategy','bhold'
    print mean,rmse, win,ntrades,last,strat,bhold
    return dcumsum