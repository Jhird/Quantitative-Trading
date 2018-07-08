# -*- coding: utf-8 -*-
"""
Created on Mon Jan 11 20:27:52 2016

TRADING STRATEGY: BENCHMARK STRATEGY - Channel Breakout
(See Page 90 of Kestner's textbook)

ALGORITHM:

* Enter long if today's close is the highest close of the past 40 days
* Exit long if today's close is the lowest in 20 days
* Enter short if today's close is the lowest in 40 days
* Exit short if today's close is the highest close in 20 days 

# JUAN'S SUGGESTION: Change the algorithm so that you only have 100 shares or
  0 shares at any time

TIMESPAN = 6 years (Jan 2010 --- Dec 2015)

@author: Jahir Gutierrez
"""

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from pandas import read_csv

#%% GET AND PREPARE DATA 

## Get SP500 data
location = os.getcwd()
data_location = location + '\\SP500_historical'
os.chdir(data_location)

## Load Data for the selected years (Adj_Close)
filename = 'Adj_Close_SP500_2010_2012.csv'
filename = os.getcwd() + '\\' + filename
Adj_Close_2010_2012 = read_csv(filename, index_col=0) # Read QSTK compatible dataframe
symbols_2010_2012 = list(Adj_Close_2010_2012.columns) # Get symbols

filename = 'Adj_Close_SP500_2013_2015.csv'
filename = os.getcwd() + '\\' + filename
Adj_Close_2013_2015 = read_csv(filename, index_col=0) # Read QSTK compatible dataframe
symbols_2013_2015 = list(Adj_Close_2013_2015.columns) # Get symbols

# Get symbols that appear in all six years
tickers = []
for s in symbols_2010_2012:
    if s in symbols_2013_2015:
        tickers.append(s)
    else:
        continue

# Remove SPY index to avoid bias
tickers.remove('SPY')

## Merge dataframes into one
Adj_Close_ALL = pd.concat([Adj_Close_2010_2012[tickers],Adj_Close_2013_2015[tickers]])
dates_ALL = Adj_Close_ALL.index
prices_ALL = Adj_Close_ALL.values.copy()

#%% GENERATE TRADING ORDERS ACCORDING TO SIGNALS

# Initialize orders list
orders = []
cash_to_spend = 1000.0 # Cash to spend on each trade

for s in tickers: # For all tickers
    have_long = False # We start with no LONG holdings
    have_short = False # We start with no SHORT holdings
    for i in range(40,len(dates_ALL)):
        d = dates_ALL[i]
        date = d.replace(' 16:00:00','') # Format date to input in .csv orders file
        date = date.split('-')
        
        if Adj_Close_ALL[s][dates_ALL[i]] >= max(Adj_Close_ALL[s][dates_ALL[i-40:i]]) and have_long == False: # If close price is the highest in the last 40 days
            #Generate Buy order (ENTER LONG)
            y = str(int(date[0]))
            m = str(int(date[1]))
            d = str(int(date[2]))
            Q = np.int(np.round(cash_to_spend / Adj_Close_ALL[s][dates_ALL[i]]))
            order = y + ',' + m + ',' + d + ',' + str(s) + ',' + 'Buy,' + str(Q)
            orders.append(order)
            have_long = True
        
        elif Adj_Close_ALL[s][dates_ALL[i]] <= min(Adj_Close_ALL[s][dates_ALL[i-20:i]]) and have_long == True: # If close price is the lowest in the last 20 days
            #Generate Sell order(EXIT LONG)
            y = str(int(date[0]))
            m = str(int(date[1]))
            d = str(int(date[2]))
            order = y + ',' + m + ',' + d + ',' + str(s) + ',' + 'Sell,' + str(Q)
            orders.append(order)
            have_long = False
        
        elif Adj_Close_ALL[s][dates_ALL[i]] <= min(Adj_Close_ALL[s][dates_ALL[i-40:i]]) and have_short == False: # If close price is the lowest in the last 40 days
            #Generate Buy order (ENTER SHORT)
            y = str(int(date[0]))
            m = str(int(date[1]))
            d = str(int(date[2]))
            Q = np.int(np.round(cash_to_spend / Adj_Close_ALL[s][dates_ALL[i]]))
            order = y + ',' + m + ',' + d + ',' + str(s) + ',' + 'Buy,' + str(Q)
            orders.append(order)
            have_short = True
        
        elif Adj_Close_ALL[s][dates_ALL[i]] >= max(Adj_Close_ALL[s][dates_ALL[i-20:i]]) and have_short == True: # If close price is the highest in the last 20 days
            #Generate Sell order(EXIT SHORT)
            y = str(int(date[0]))
            m = str(int(date[1]))
            d = str(int(date[2]))
            order = y + ',' + m + ',' + d + ',' + str(s) + ',' + 'Sell,' + str(Q)
            orders.append(order)
            have_short = False
            
        else:
            continue

#%% Write CSV file
os.chdir(location)
filename = 'TS_BENCHMARK_channel_breakout_SP500_orders.csv'
f = open(filename,'w')
for line in orders:
    f.write(line)
    f.write('\n')
f.close()


##%% PLOT SAMPLE CURVE
#s = 'ACAD'
#plt.figure()
#plt.plot(Adj_Close_ALL[s][dates_ALL[20:60]])
#plt.plot(moving_avg[s][dates_ALL[20:60]])
#plt.plot(bollinger_up[s][dates_ALL[20:60]])
#plt.plot(bollinger_down[s][dates_ALL[20:60]])
#plt.legend(['Adj_Close','Avg','BollUp','BollDown'])
#plt.show()

#plt.figure()
#plt.plot(bollinger_values[s])
#plt.legend(['BollValues'])
#plt.show()
