

import warnings
warnings.simplefilter('ignore')

import numpy as np
import pandas as pd
import multiprocessing as mp
import pandas.io.data as web
import matplotlib.pyplot as plt


def compTrade(dt):
    d=0.001
    dt['reg']=np.where(dt['dmacd']>d,1,0)
    dt['reg']=np.where(dt['dmacd']<-d,-1,dt['reg'])
    dt['strategy']=dt['reg'].shift(1)*dt['market']
    return dt
    
def getSymbols(h5):
    l=[]
    for c in h5.keys():
        l.append(h5[c]['Adj Close'].columns.values)
        
    return [item for items in l for item in items]  

def getClose(h5,sym):
    df = pd.DataFrame()
    for c in h5.keys():
        for i in h5[c]['Adj Close'].columns:
            if sym == i:
                df['Adj Close']=h5[c]['Adj Close'][i]
        
    return df

def fromYahoo(name,sdate='2015-01-01',edate='2015-12-31'):
    
    DT = web.DataReader(name, data_source='yahoo',
                 start=sdate,end=edate)    
    return DT

def macd(DT):
    
    DT['Date'] = pd.to_datetime( DT.index)
    tempds = DT.sort('Date',ascending = True )
    firstDate = tempds['Date'][0]
    DT['CloseN'] = DT['Adj Close']/DT['Adj Close'][firstDate]
    
    cs = tempds['Adj Close']
    firstClose=tempds['Adj Close'][firstDate]
    macd=pd.ewma(cs,span=12)-pd.ewma(cs,span=26)
    signal=pd.ewma(macd,span=9)
    
    DT['macd'] = macd
    DT['signal'] = signal
    DT['dmacd'] = macd-signal
    DT['market']=np.log(cs/cs.shift(1))
    return compTrade(DT)


def plotMacd(DT):
    

    figsize=(20, 10)
    fig, axs1 = plt.subplots(1,1,figsize=figsize)
    fig, axs2 = plt.subplots(1,1,figsize=figsize)
    fig, axs3 = plt.subplots(1,1,figsize=figsize)
    fig, axs4 = plt.subplots(1,1,figsize=figsize)
            
    DT['CloseN'].plot(ax=axs1, grid=True)
    DT['macd'].plot(ax=axs2, grid=True)
    DT['signal'].plot(ax=axs2, grid=True)
    DT['dmacd'].plot(ax=axs3, grid=True)
    DT['reg'].plot(ax=axs3, grid=True)
    DT[['market','strategy']].cumsum().apply(np.exp).plot(ax=axs4, grid=True)
    
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

    res={}
    res['meanpct']=mean
    res['rmsepct']=rmse
    res['win']=win
    res['strategy']=strat
    res['buyhold']=bhold
    res['ntrades']=ntrades
    res['totwinpct']=last
    return dcumsum,res
    
def doCumsumonSymbols(p):
    filename,symbols,start,end=p    
    h5 = pd.HDFStore(filename, 'r')           
    fd=pd.DataFrame()
    for sym in symbols:
        dt0=getClose(h5,sym)[start:end]

        dt = macd(dt0) 
        dcs,res=doCumsum(dt)
        res['sym']=sym
        tfd=pd.DataFrame(res,index=[sym])
        fd=fd.append(tfd)
    return fd
    
def parallelCumsum(filename,syms,start,end,procs=1):
    alists=[]
    nsym=len(syms)
    f=nsym/procs
    if nsym%procs >0:
        f=f+1
    for i in range(0,procs):
        alists.append((filename,syms[i*f:(i+1)*f],start,end))
    #print alists
    pool = mp.Pool(processes=procs)
    res=pool.map(doCumsumonSymbols,alists)

    df=pd.DataFrame()
    for r in res:
        df=df.append(r)
    df=df.sort('totwinpct',ascending=False) 
    return df    