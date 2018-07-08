# -*- coding: utf-8 -*-
"""
Created on Mon Jan 11 20:27:52 2016

TRADING STRATEGY: Use Bollinger Bands as Technical Indicator

Up Bollinger Band = 20-day moving average + k*SD
Down Bollinger Band = 20-day moving average - k*SD

Sell and wait IF closing_price > Up BD after you've made a purchase crossing the
moving_avg
Buy and hold IF closing_price < Down BD you sell with price > moving_avg    

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

#%% CALCULATE MOVING AVERAGE, MOVING STD AND BOLLINGER BANDS
wind_size = 20 # Size of window
k = 2.0 # Distance of Bollinger bands from moving average in number of STD

moving_avg = pd.rolling_mean(Adj_Close_ALL,wind_size)
moving_std = pd.rolling_std(Adj_Close_ALL,wind_size)
bollinger_up = moving_avg + (k * moving_std)
bollinger_down = moving_avg - (k * moving_std)

bollinger_values = (Adj_Close_ALL - moving_avg)/moving_std
#%% GENERATE TRADING ORDERS ACCORDING TO SIGNALS

# Initialize orders list
orders = []
cash_to_spend = 1000.0

for s in tickers: # For all tickers
    have_stocks = 'no' # We start with no holdings
    bol = '' # We start with no transitions across the Bollinger bands
    for d in dates_ALL: # For all dates in dataframe
        
        date = d.replace(' 16:00:00','') # Format date to input in .csv orders file
        date = date.split('-')
        
        if np.isnan(bollinger_values[s][d]): # ignore if NAN
            continue
        
        elif bollinger_values[s][d] <= -k and have_stocks == 'no' and bol=='': # If price goes below down Bollinger
            #Generate Buy order
            y = str(int(date[0]))
            m = str(int(date[1]))
            da = str(int(date[2]))
            Q = np.int(np.round(cash_to_spend / Adj_Close_ALL[s][d]))
            order = y + ',' + m + ',' + da + ',' + str(s) + ',' + 'Buy,' + str(Q)
            orders.append(order)
            have_stocks = 'yes'
            bol = 'down'
        
        elif bollinger_values[s][d] > -k and bollinger_values[s][d] < k and Adj_Close_ALL[s][d] >= moving_avg[s][d] and have_stocks == 'yes' and bol == 'down': # If you cross the mean line upwards
            #Generate Sell order
            y = str(int(date[0]))
            m = str(int(date[1]))
            da = str(int(date[2]))
            order = y + ',' + m + ',' + da + ',' + str(s) + ',' + 'Sell,' + str(Q)
            orders.append(order)
            have_stocks = 'no'
            bol = ''
        
        elif bollinger_values[s][d] >= k and have_stocks == 'yes' and bol=='up': # If price goes above up Bollinger 
            #Generate Sell order
            y = str(int(date[0]))
            m = str(int(date[1]))
            da = str(int(date[2]))
            order = y + ',' + m + ',' + da + ',' + str(s) + ',' + 'Sell,' + str(Q)
            orders.append(order)
            have_stocks = 'no'
            bol = ''
        
        elif bollinger_values[s][d] < k and bollinger_values[s][d] > -k and Adj_Close_ALL[s][d] <= moving_avg[s][d] and have_stocks == 'no' and bol == '': # If you cross the mean line downwards
            #Generate Buy order
            y = str(int(date[0]))
            m = str(int(date[1]))
            da = str(int(date[2]))
            Q = np.int(np.round(cash_to_spend / Adj_Close_ALL[s][d]))
            order = y + ',' + m + ',' + da + ',' + str(s) + ',' + 'Buy,' + str(Q)
            orders.append(order)
            have_stocks = 'yes'
            bol = 'up'
            
        else:
            continue

#%% Write CSV file
os.chdir(location)
filename = 'TS_bollinger_bands_SP500_orders.csv'
f = open(filename,'w')
for line in orders:
    f.write(line)
    f.write('\n')
f.close()


##%% PLOT SAMPLE CURVE
#plt.figure()
#plt.plot(Adj_Close_ALL[s][dates_ALL[20:60]])
#plt.plot(moving_avg[s][dates_ALL[20:60]])
#plt.plot(bollinger_up[s][dates_ALL[20:60]])
#plt.plot(bollinger_down[s][dates_ALL[20:60]])
#plt.legend(['Adj_Close','Avg','BollUp','BollDown'])
#plt.show()
#
#plt.figure()
#plt.plot(bollinger_values[s])
#plt.legend(['BollValues'])
#plt.show()
