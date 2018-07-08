# -*- coding: utf-8 -*-
"""
Created on Mon Jan 11 20:27:52 2016

TRADING STRATEGY: Use Bollinger Bands as Technical Indicator

Up Bollinger Band = 20-day moving average + 1 SD
Down Bollinger Band = 20-day moving average - 1 SD

Sell and wait IF closing_price > Up BD
Buy and hold IF closing_price < Down BD    

TIMESPAN = 3 years (Jan 2013 --- Dec 2015)

@author: Jahir Gutierrez
"""

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from pandas import read_csv

#%% GET AND PREPARE DATA 

## Get IBB data
os.chdir("C:\\Users\\Jahir Gutierrez\\Google Drive\\Andellor\\Quantitative Trading Project (QTP)\\Software\\Quant Python Scripts\\IBB_historical")

## Load Data for the selected years (Adj_Close)
filename = 'Adj_Close' + '_IBB_' + str(2013) + '.csv'
filename = os.getcwd() + '\\' + filename
Adj_Close_2013 = read_csv(filename, index_col=0) # Read QSTK compatible dataframe
symbols_2013 = list(Adj_Close_2013.columns) # Get symbols

filename = 'Adj_Close' + '_IBB_' + str(2014) + '.csv'
filename = os.getcwd() + '\\' + filename
Adj_Close_2014 = read_csv(filename, index_col=0) # Read QSTK compatible dataframe
symbols_2014 = list(Adj_Close_2014.columns) # Get symbols

filename = 'Adj_Close' + '_IBB_' + str(2015) + '.csv'
filename = os.getcwd() + '\\' + filename
Adj_Close_2015 = read_csv(filename, index_col=0) # Read QSTK compatible dataframe
symbols_2015 = list(Adj_Close_2015.columns) # Get symbols

# Get symbols that appear in all three years
tickers = []
for s in symbols_2013:
    if s in symbols_2014 and s in symbols_2015:
        tickers.append(s)
    else:
        continue

# Remove IBB index to avoid bias
tickers.remove('IBB')

## Merge dataframes into one
Adj_Close_ALL = pd.concat([Adj_Close_2013[tickers],Adj_Close_2014[tickers],Adj_Close_2015[tickers]])
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
shares_to_buy = 100

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
            d = str(int(date[2]))
            order = y + ',' + m + ',' + d + ',' + str(s) + ',' + 'Buy,' + str(shares_to_buy)
            orders.append(order)
            have_stocks = 'yes'
            bol = 'down'
        
        elif bollinger_values[s][d] > -k and bollinger_values[s][d] < k and Adj_Close_ALL[s][d] >= moving_avg[s][d] and have_stocks == 'yes' and bol == 'down': # If you cross the mean line upwards
            #Generate Sell order
            y = str(int(date[0]))
            m = str(int(date[1]))
            d = str(int(date[2]))
            order = y + ',' + m + ',' + d + ',' + str(s) + ',' + 'Sell,' + str(shares_to_buy)
            orders.append(order)
            have_stocks = 'no'
            bol = ''
        
        elif bollinger_values[s][d] >= k and have_stocks == 'yes' and bol=='up': # If price goes above up Bollinger 
            #Generate Sell order
            y = str(int(date[0]))
            m = str(int(date[1]))
            d = str(int(date[2]))
            order = y + ',' + m + ',' + d + ',' + str(s) + ',' + 'Sell,' + str(shares_to_buy)
            orders.append(order)
            have_stocks = 'no'
            bol = ''
        
        elif bollinger_values[s][d] < k and bollinger_values[s][d] > -k and Adj_Close_ALL[s][d] <= moving_avg[s][d] and have_stocks == 'no' and bol == '': # If you cross the mean line downwards
            #Generate Buy order
            y = str(int(date[0]))
            m = str(int(date[1]))
            d = str(int(date[2]))
            order = y + ',' + m + ',' + d + ',' + str(s) + ',' + 'Buy,' + str(shares_to_buy)
            orders.append(order)
            have_stocks = 'yes'
            bol = 'up'
            
        else:
            continue

#%% Write CSV file
os.chdir("C:\\Users\\Jahir Gutierrez\\Google Drive\\Andellor\\Quantitative Trading Project (QTP)\\Software\\Quant Python Scripts")
filename = 'TS_bollinger_bands_orders.csv'
f = open(filename,'w')
for line in orders:
    f.write(line)
    f.write('\n')
f.close()


#%% PLOT SAMPLE CURVE
s = 'ACAD'
plt.figure()
plt.plot(Adj_Close_ALL[s][dates_ALL[20:60]])
plt.plot(moving_avg[s][dates_ALL[20:60]])
plt.plot(bollinger_up[s][dates_ALL[20:60]])
plt.plot(bollinger_down[s][dates_ALL[20:60]])
plt.legend(['Adj_Close','Avg','BollUp','BollDown'])
plt.show()

plt.figure()
plt.plot(bollinger_values[s])
plt.legend(['BollValues'])
plt.show()
