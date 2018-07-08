# -*- coding: utf-8 -*-
"""
Market Simulator for Quant
- December 6th 2015
- Jahir Gutierrez 

DESCRIPTION
Python Script that must be run from command line
-example-
python marketsim.py 1000000 orders.csv values.csv GSPC

Inputs:
    -[0] name of this script (marketsim.py)
    -[1] initial cash (1,000,000)
    -[2] name of orders file (orders.csv)
    -[3] name of file with portfolio values over time (values.csv)
    -[4] name of market ticker to compare with and the options are:
         DJI = Dow Jones Industrial Average
         NYA = NYSE Average
         IXIC = NASDAQ Composite
         NDX = NASDAQ 100
         GSPC = SP500
         SPY = SPDR S&P 500 ETF
         NBI = NASDAQ Biotech
         IBB = iShares Biotech

Output:
    - Performance of portfolio against market
    - Graph of performance (normalized values)
"""

#%% READ PACKAGES
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pandas import DataFrame, read_csv, Series
import os
import time
import sys
from dateutil.parser import parse
from matplotlib.patches import Ellipse
import matplotlib
from matplotlib.pyplot import figure,show
import matplotlib.pyplot as plt
import matplotlib.dates as md
import dateutil
from yahoo_finance import Share
import math
import copy
import QSTK.qstkstudy.EventProfiler as ep

#%% READ DATES AND SYMBOLS

# LOAD AND PREPARE DATAFRAME (df) FOR ANALYSIS
Location = os.getcwd()
orders_file = str(sys.argv[2])
Location = Location + '\\' + orders_file
df = pd.read_csv(Location,header=None)
df.columns = ['Year','Month','Date','Symbol','Buy/Sell','Quantity']
df = df.sort_index(by=['Year','Month','Date'],ascending=[True,True,True])

# MAKE LISTS OF SYMBOLS AND DATES
dates = []
symbols = []
for i in range(np.size(df,0)):
    date = dt.datetime(df['Year'][i],df['Month'][i],df['Date'][i]) 
    symbol = df['Symbol'][i]
    dates.append(date)
    symbols.append(symbol)
symbols = list(set(symbols))
symbols.sort()

#%% Make dataframes compatible with QSTK
tickers = symbols
today = time.strftime("%Y-%m-%d")
startdate = str(min(dates))
startdate = startdate.replace(" 00:00:00","")
enddate = str(max(dates))
enddate = enddate.replace(" 00:00:00","")

stocks = []
for ticker in tickers:
    stocks.append(Share(ticker))

historical_data = []
for stock in stocks:
    historical_data.append(stock.get_historical(startdate,enddate))

yahooF_keys = ['Adj_Close','Close','High','Low','Open','Volume']


# Make list of values to be used later for constructing appropriate data frames
def makeListFromYFkey(stock_historical_data,yahooF_key):
    l = []
    for i in range(len(stock_historical_data)):
        l.append(round(float(stock_historical_data[i][yahooF_key]),2))
    return l

def makeListOfDates(stock_historical_data):
    d = []
    for i in range(len(stock_historical_data)):
        d.append(stock_historical_data[i]['Date'])
    return d

# Create Universal Time Stamps
trading_dates = makeListOfDates(historical_data[0])
time_stamps = []
for date in trading_dates:
    time_stamps.append(pd.tslib.Timestamp(date + ' 16:00:00')) 

    
# Create Dataframes for a specific Key for all stocks
def makeDataFrameFromYFkey(yahooF_key):
    data = {} 
    for i in range(len(tickers)):
        l = makeListFromYFkey(historical_data[i],yahooF_key)
        data[tickers[i]] = Series(l, index=time_stamps)
    df = DataFrame(data)
    return df.sort_index()

# Create Dictionary of DataFrames as required by QSTK
list_dataframes = []
for k in yahooF_keys:
    list_dataframes.append(makeDataFrameFromYFkey(k))


# This is the final data you can use with the QSTK library
qstk_data = dict(zip(yahooF_keys,list_dataframes))
for s_key in yahooF_keys:
    qstk_data[s_key] = qstk_data[s_key].fillna(method='ffill')
    qstk_data[s_key] = qstk_data[s_key].fillna(method='bfill')
    qstk_data[s_key] = qstk_data[s_key].fillna(1.0)

#%% CREATE A DATAFRAME WITH THE PRICES OF THE STOCKS WITHIN THE TIME PERIOD 
### BETWEEN START AND END DATES
dt_start = min(dates)
dt_end = max(dates) + dt.timedelta(days=1)
dt_timeofday = dt.timedelta(hours=16)
ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt_timeofday)    
prices = qstk_data['Adj_Close']

# CREATE TRADE MATRIX
trade_matrix = pd.DataFrame(data=0,index = ldt_timestamps,columns=symbols)
for i in range(len(dates)):
    # Get date of order
    date = str(pd.tslib.Timestamp(dates[i]))
    date = date.replace("00:00:00","16:00:00")
    symbol = df['Symbol'][i]
    quantity = df['Quantity'][i]
    if df['Buy/Sell'][i] == 'Buy':
        coeff = 1
    elif df['Buy/Sell'][i] == 'Sell':
        coeff = -1
    trade_matrix[symbol][date] = trade_matrix[symbol][date] + (coeff * quantity)

# Initialize Cash
init_cash = float(str(sys.argv[1]))#1000000.0
c = init_cash
cash = pd.DataFrame(data=0,index = ldt_timestamps,columns=['Cash'])
for i in range(len(ldt_timestamps)):
    # Get date of order
    date = str(ldt_timestamps[i])
    c = c + sum(np.array(prices.loc[date])*np.array(trade_matrix.loc[date])*-1)
    num_transactions = np.size(np.nonzero(np.array(trade_matrix.loc[date])))
    c = c - (20.00 * num_transactions)
    cash.loc[date] = c

# Get initial holdings
ts = str(ldt_timestamps[0])
init_holdings = pd.DataFrame(data=0,index=[ts],columns=symbols)

for i in range(len(symbols)):
    test = df[df['Symbol'] == symbols[i]]
    buy_or_sell = test['Buy/Sell'][test.index[0]]
    if buy_or_sell == 'Buy':
        init_holdings[symbols[i]][str(ldt_timestamps[0])] = 0
    elif buy_or_sell == 'Sell':
        init_holdings[symbols[i]][str(ldt_timestamps[0])] = test['Quantity'][test.index[0]]

# CREATE HOLDINGS MATRIX FROM TRADE MATRIX
holdings = pd.DataFrame(data=0,index = ldt_timestamps,columns=trade_matrix.columns)
h = np.array(init_holdings)

for i in range(len(ldt_timestamps)):
    date = str(ldt_timestamps[i])
    h = h + np.array(trade_matrix.loc[date])
    holdings.loc[date] = h

prices['CASH'] = 1.0
trade_matrix['CASH'] = cash
holdings['CASH'] = cash

# COMPUTE THE VALUE OF THE PORTAFOLIO OVER TIME
value = pd.DataFrame(data=0,index = ldt_timestamps,columns=['Value'])

for i in range(len(ldt_timestamps)):
    date = str(ldt_timestamps[i])
    v = 0
    for i in range(len(symbols)):
        v = v + prices[symbols[i]][date]*holdings[symbols[i]][date]
    v = v + holdings['CASH'][date]
    value.loc[date] = v

# Write Values to csv file
filename = str(sys.argv[3])
f = open(filename,'w')
for i in range(len(ldt_timestamps)):
    y = str(ldt_timestamps[i].year)
    m = str(ldt_timestamps[i].month)
    d = str(ldt_timestamps[i].day)
    f.write(y+',')
    f.write(m+',')
    f.write(d+',')
    f.write(str(float(value.loc[str(ldt_timestamps[i])])))
    f.write('\n')
f.close()

# ASSESS PORTFOLIO AND $SPX
def assessPortfolio(na_price,allocations):
    na_normalized = (na_price / na_price[0,:]) * allocations
    daily_ret = np.zeros([np.size(na_price,0),1])
    for i in range(np.size(daily_ret,0)):
        daily_ret[[i]] = sum(na_normalized[i,:])
    norm_daily_ret = daily_ret.copy()
    tsu.returnize0(norm_daily_ret)
    daily_ret_avg = np.mean(norm_daily_ret)
    vol = np.std(norm_daily_ret)
    sharpe = np.sqrt(252)*daily_ret_avg/vol
    cum_ret = float(daily_ret[-1])
    return vol, daily_ret_avg, sharpe, cum_ret

# Portfolio
na_value = np.array(value)
allocations = [1]
vol, daily_ret_avg, sharpe, cum_ret = assessPortfolio(na_value,allocations)

#%% Output

# CREATE DATAFRAME WITH MARKET DATA
if str(sys.argv[4]) == 'SPY' or str(sys.argv[4]) == 'IBB':
    market_ticker = str(sys.argv[4])
else:
    market_ticker = '^' + str(sys.argv[4])

market = Share(market_ticker)
market_historical_data = market.get_historical(startdate,enddate)

# Create Dataframes for a specific Key for all stocks
market_data = {} 
l = makeListFromYFkey(market_historical_data,'Adj_Close')
market_data[market_ticker] = Series(l, index=time_stamps)
market_df = DataFrame(market_data)
market_df.sort_index()

market_qstk_data = dict(zip(['Adj_Close'],[market_df]))
market_qstk_data['Adj_Close'] = market_qstk_data['Adj_Close'].fillna(method='ffill')
market_qstk_data['Adj_Close'] = market_qstk_data['Adj_Close'].fillna(method='bfill')
market_qstk_data['Adj_Close'] = market_qstk_data['Adj_Close'].fillna(1.0)

market_prices = market_qstk_data['Adj_Close']

# Market ($SPX)
na_market = np.array(market_prices)
vol_market,daily_ret_avg_market,sharpe_market,cum_ret_market = assessPortfolio(na_market,allocations)

###############################################################3
first_date = str(pd.tslib.Timestamp(min(dates)))
last_date = str(pd.tslib.Timestamp(max(dates)))
first_date = first_date.replace(" 00:00:00","")
last_date = last_date.replace(" 00:00:00","")
print "The initial CASH in this backtest was -- $USD %d \n" % init_cash
print "The final value of the portfolio is -- $USD %d \n" % float(na_value[-1])
print "Details of the Performance of the portfolio : \n"
print "Data Range : %s to %s \n" % (first_date, last_date)
print "Sharpe Ratio of Fund : %f " % sharpe
print "Sharpe Ratio of Benchmark : %f \n" % sharpe_market
print "Total Return of Fund : %f " % cum_ret
print "Total Return of Benchmark : %f \n" % cum_ret_market
print "Standard Deviation of Fund : %f " % vol
print "Standard Deviation of Benchmark : %f \n" % vol_market
print "Average Daily Return of Fund : %f " % daily_ret_avg
print "Average Daily Return of Benchmark : %f \n" % daily_ret_avg_market

filename = orders_file.replace('orders.csv','performance.txt')
f = open(filename,'w')
f.write("The initial CASH in this backtest was -- $USD %d \n" % init_cash)
f.write("The final value of the portfolio is -- $USD %d \n" % float(na_value[-1]))
f.write("Details of the Performance of the portfolio : \n")
f.write("Data Range : %s to %s \n" % (first_date, last_date))
f.write("\n")
f.write("Sharpe Ratio of Fund : %f " % sharpe)
f.write("\n")
f.write("Sharpe Ratio of Benchmark : %f \n" % sharpe_market)
f.write("\n")
f.write("Total Return of Fund : %f " % cum_ret)
f.write("\n")
f.write("Total Return of Benchmark : %f \n" % cum_ret_market)
f.write("\n")
f.write("Standard Deviation of Fund : %f " % vol)
f.write("\n")
f.write("Standard Deviation of Benchmark : %f \n" % vol_market)
f.write("\n")
f.write("Average Daily Return of Fund : %f " % daily_ret_avg)
f.write("\n")
f.write("Average Daily Return of Benchmark : %f \n" % daily_ret_avg_market)

f.close()

X = np.concatenate((na_value/init_cash, na_market/na_market[0]), axis=1)
X_normalized = X
plt.figure(figsize=(15,10))
plt.plot(ldt_timestamps, X_normalized)
plt.legend(['Portfolio','Benchmark'+' (' + market_ticker +')'])
plt.ylabel('Normalized Adjusted Close')
plt.xlabel('Date')
plt.title('Comparison of Portfolio VS Market', bbox={'facecolor':'0.8', 'pad':5})
ordFile = orders_file.replace('orders.csv','comparisonVSmarket_plot')
plt.savefig(ordFile + '.png', bbox_inches='tight')
plt.savefig(ordFile + '.pdf', bbox_inches='tight')