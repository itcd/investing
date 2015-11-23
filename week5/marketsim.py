'''
(c) 2011, 2012 Georgia Tech Research Corporation
This source code is released under the New BSD license.  Please see
http://wiki.quantsoftware.org/index.php?title=QSTK_License
for license details.

Created on January, 24, 2013

@author: Sourabh Bajaj
@contact: sourabhbajaj@gatech.edu
@summary: An example to show how dataAccess works.
'''

import sys
import csv

# QSTK Imports
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da

# Third Party Imports
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import pandas
from blaze import nan
from numpy import NaN
import math
import numpy as np

if __name__ == '__main__':
    print 'Number of arguments:', len(sys.argv), 'arguments.'
    print 'Argument List:', str(sys.argv)
    if len(sys.argv)>=4:
        cash=sys.argv[1]
        orderfile=sys.argv[2]
        valuefile=sys.argv[3]

    # read csv file and format the lists
    symbols=[]
    datestrlist=[]
    rows=[]
    with open(orderfile, 'rb') as f:
        reader = csv.reader(f,delimiter=',')
        for row in reader:
            print row
            row=[r.strip() for r in row]
            rows.append(row)
            symbols.append(row[3])
            s=str(row[:3])
            s=s.replace('\'', '')
            s=s.replace('[', '')
            s=s.replace(']', '')
            datestrlist.append(s)

    # remove duplicate symbols and dates, and get start and end dates
    symbols = list(set(symbols))
    symbols.sort()
    datestrlist = list(set(datestrlist))
    print(symbols)

    dates=[]
    for d in datestrlist:
        l=[int(x) for x in d.split(',')]
        dates.append(l)
    dates.sort()
    d1=dates[0]
    d2=dates[-1]
    print(d1,d2)

    '''
    Year
    Month
    Day
    Symbol
    BUY or SELL
    Number of Shares
    '''

    cash=float(cash)
    rows2=[]
    indices=[]

    # merge lines of same dates
    for i in range(len(rows)):
        r=rows[i]
        s=[0 for j in symbols]
        if r[4].lower()=='sell':
            r[5]='-'+r[5]
        s[symbols.index(r[3])]=int(r[5])
        date_object = datetime.strptime(r[0]+'-'+r[1]+'-'+r[2], '%Y-%m-%d')+dt.timedelta(hours=16)
        if i>0 and date_object==indices[-1]:
            for j in range(len(symbols)):
                rows2[-1][j]+=s[j]
        else:
            indices.append(date_object)
            rows2.append(s)
    
    # create data frame and sort by index
    df_trade = pandas.DataFrame(rows2, columns=symbols, index=indices)
    df_trade=df_trade.sort_index()
    df_trade.to_csv('~tradematrix.csv')

    # load data from Yahoo
    dt_start = dt.datetime(d1[0], d1[1], d1[2])
    dt_end = dt.datetime(d2[0], d2[1], d2[2])
    dt_end = dt_end + dt.timedelta(days=1) 
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt.timedelta(hours=16))
    
    dataobj = da.DataAccess('Yahoo')
    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    ldf_data = dataobj.get_data(ldt_timestamps, symbols+['$SPX'], ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))
    
    for s_key in ls_keys:
        d_data[s_key] = d_data[s_key].fillna(method = 'ffill')
        d_data[s_key] = d_data[s_key].fillna(method = 'bfill')
        d_data[s_key] = d_data[s_key].fillna(1.0)
    
    # use adjusted close prices
    df_close=d_data['close']
    ldt_timestamps = df_close.index
    
    # time series of orders
    timeseries=pd.Series([0 for i in df_trade.index],index=df_trade.index)
    cumulative=df_trade.copy();

    # calculate cash on each order day
    holdings=[]
    for i in range(len(timeseries)):
        if i==0:
            balance=cash
            cumulative.ix[timeseries.index[i]]=df_trade.ix[timeseries.index[i]]
        else:
            balance=timeseries[i-1]
            cumulative.ix[timeseries.index[i]]=df_trade.ix[timeseries.index[i]]+cumulative.ix[timeseries.index[i-1]]

        price=[df_close[s].ix[timeseries.index[i]] for s in symbols]
        order=df_trade.ix[timeseries.index[i]]
        h=cumulative.ix[timeseries.index[i]]
        holdings.append(h)
        for j in range(len(order)):
            balance-=order[j]*price[j]
        
        timeseries[i]=balance

    times=[]
    for i in range(len(ldt_timestamps)):
        if ldt_timestamps[i] >= timeseries.index[0] and ldt_timestamps[i]<=timeseries.index[-1]:
            times.append(ldt_timestamps[i])

    # add columns to the holding matrix
    results = pandas.DataFrame(times, columns=['Date'], index=times)
    results['Fund']=NaN
    results['Cash']=NaN
    for s in symbols:
        results[s]=NaN
    results = results.drop('Date', 1)
    
#     for index, row in timeseries.iteritems():
#         results.set_value(index, 'Cash', row)

    # forward fill holding matrix with trade matrix
    for i in range(len(timeseries)):
        index=timeseries.index[i]
        results.set_value(index, 'Cash', timeseries[i])
        for s in symbols:   
            results.set_value(index, s, holdings[i][s])
    results=results.fillna(method = 'ffill')

    # calculate daily balance
    for t in times:
#         print t
        price=[df_close[s].ix[t] for s in symbols]
        h=[results.ix[t,s] for s in symbols]
        port=[price[j]*h[j] for j in range(len(symbols))]
        total=sum(port)+results.ix[t,'Cash']
        results.set_value(t, 'Fund', total)

    results.to_csv('~holdingmatrix.csv')
    df_close['Fund']=results['Fund']

    trading_days = 252
    na_price = df_close.values
    na_rets = na_price / na_price[0, :]
    
    # SPY  
    weights=[0 for s in symbols]+[1,0]
    a=[np.sum(i*weights) for i in na_rets]
    b = tsu.returnize0(a).flatten()
    mean=np.mean(b)
    std=np.std(b) 
    cum_ret=a[len(a)-1]/a[0]-1
    daily_ret=mean
    vol=std
    sharpe=math.sqrt(trading_days)*mean/std
    sharpe0=sharpe
    total0=cum_ret+1
    std0=vol
    daily0=daily_ret
    
    # Fund
    weights=[0 for s in symbols]+[0,1]
    a=[np.sum(i*weights) for i in na_rets]
    b = tsu.returnize0(a).flatten()
    mean=np.mean(b)
    std=np.std(b) 
    cum_ret=a[len(a)-1]/a[0]-1
    daily_ret=mean
    vol=std
    sharpe=math.sqrt(trading_days)*mean/std
    sharpe1=sharpe
    total1=cum_ret+1
    std1=vol
    daily1=daily_ret
    
    print('Sharpe Ratio of Fund',sharpe1)
    print('Sharpe Ratio of $SPX',sharpe0)
    print('Total Return of Fund',total1)
    print('Total Return of $SPX',total0)
    print('Standard Deviation of Fund',std1)
    print('Standard Deviation of $SPX',std0)
    print('Average Daily Return of Fund',daily1)
    print('Average Daily Return of $SPX',daily0)

'''
The final value of the portfolio using the sample file is -- 2011,12,20,1133860

Details of the Performance of the portfolio :

Data Range :  2011-01-10 16:00:00  to  2011-12-20 16:00:00

Sharpe Ratio of Fund : 1.21540462111
Sharpe Ratio of $SPX : 0.0183391412227

Total Return of Fund :  1.13386
Total Return of $SPX : 0.97759401457

Standard Deviation of Fund :  0.00717514512699
Standard Deviation of $SPX : 0.0149090969828

Average Daily Return of Fund :  0.000549352749569
Average Daily Return of $SPX : 1.72238432443e-05
''' 
