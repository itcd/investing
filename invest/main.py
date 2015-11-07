'''
Created on 7 Nov 2015

@author: joe
'''

import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da

import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import math
from numpy import inf
from matplotlib.pyplot import axis

# The function should return:
# Standard deviation of daily returns of the total portfolio
# Average daily return of the total portfolio
# Sharpe ratio (Always assume you have 252 trading days in an year. And risk free rate = 0) of the total portfolio
# Cumulative return of the total portfolio
def simulate(dt_start, dt_end, ls_symbols, weights):
    trading_days = 252
    dt_timeofday = dt.timedelta(hours=16)
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt_timeofday)
    
    c_dataobj = da.DataAccess('Yahoo')
    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    ldf_data = c_dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))
    
    na_price = d_data['close'].values
    na_rets = na_price / na_price[0, :]
    
    a=[np.sum(i*weights) for i in na_rets]
    b = tsu.returnize0(a).flatten()
    mean=np.mean(b)
    std=np.std(b)
    
    cum_ret=a[len(a)-1]/a[0]-1
    daily_ret=mean
    vol=std
    sharpe=math.sqrt(trading_days)*mean/std
    return vol,daily_ret,sharpe,cum_ret

def countChange(money, coins):
    return change(money,coins,[],0)

def change(money, coins, changes, index):
    if(index==3):
        changes.append(money)
        return [changes]
    
    if(money<=0 and index<3):
        changes.append(money)
        return change(money,coins,changes,index+1)

    changelist=[]
    for m in coins:
        if(money>=m):
            c2=changes[:]
            c2.append(m)  
            changelist += change(money-m,coins,c2,index+1)
    return changelist

'''''
Start Date: January 1, 2011
End Date: December 31, 2011
Symbols: ['AAPL', 'GLD', 'GOOG', 'XOM']
Optimal Allocations: [0.4, 0.4, 0.0, 0.2]
Sharpe Ratio: 1.02828403099
Volatility (stdev of daily returns):  0.0101467067654
Average Daily Return:  0.000657261102001
Cumulative Return:  1.16487261965

Start Date: January 1, 2010
End Date: December 31, 2010
Symbols: ['AXP', 'HPQ', 'IBM', 'HNZ']
Optimal Allocations:  [0.0, 0.0, 0.0, 1.0]
Sharpe Ratio: 1.29889334008
Volatility (stdev of daily returns): 0.00924299255937
Average Daily Return: 0.000756285585593
Cumulative Return: 1.1960583568
'''
if __name__ == '__main__':
    start = dt.datetime(2010, 1, 1)
    end = dt.datetime(2010, 12, 31)
    symbols = ['AXP', 'HPQ', 'IBM', 'HNZ']
    w = [0.4, 0.4, 0.0, 0.2]
    vol, daily_ret, sharpe, cum_ret=simulate(start,end,symbols,w)
    print('Sharpe Ratio: ',sharpe)
    print('Volatility: ',vol)
    print('Average Daily Return: ',daily_ret)
    print('Cumulative Return: ',cum_ret)
    
    coins=np.arange(0,1.1,0.1).tolist()
    weightlist=countChange(1,coins)
    r=[simulate(start,end,symbols,w)+(w,) for w in weightlist]
    
    s=0
    for (vol, daily_ret, sharpe, cum_ret, w) in r:
        if(sharpe>s):
            s=sharpe
            weight=w
    print('Optimal Allocations: ', weight, 'Sharpe Ratio: ', s)



#     trading_days = 252
#     ls_symbols = ['AAPL', 'GLD']
#     weights=[0.65,0.35]
#     dt_start = dt.datetime(2011, 1, 1)
#     dt_end = dt.datetime(2011, 12, 31)
#  
#     dt_timeofday = dt.timedelta(hours=16)
#     ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt_timeofday)
#       
#     c_dataobj = da.DataAccess('Yahoo')
#     ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
#     ldf_data = c_dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
#     d_data = dict(zip(ls_keys, ldf_data))
#       
#     na_price = d_data['close'].values
# #     np.savetxt('close_price.txt', na_price,fmt='%g', delimiter=',')
#     na_normalized_price = na_price / na_price[0, :]
#     na_rets = na_normalized_price.copy()
#       
#     a=[np.sum(i*weights) for i in na_rets]
#     b = tsu.returnize0(a).flatten()
#     #     print(type(a),type(b))
#     print('annual return=',a[len(a)-1]/a[0]-1)
#     m=np.mean(b)
#     s=np.std(b)
#     print('mean=',m,' std=',s)
#     print('sharpe=',math.sqrt(trading_days)*m/s)
#      
#     ls_symbols.append('fund')
#     x=np.asarray(a).shape
#     ar=np.asarray(a).reshape((x[0],1))
# #     print(na_rets.shape,ar.shape)
#     c=np.concatenate((na_rets,ar), axis=1)
#     plt.clf()
#     plt.plot(ldt_timestamps, c)
#     plt.legend(ls_symbols)
#     plt.ylabel('Adjusted Close')
#     plt.xlabel('Date')
# #     plt.show()
