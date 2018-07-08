# -*- coding: utf-8 -*-
"""
Created on Sun Jan 17 14:04:39 2016

@author: Jahir Gutierrez
"""
#%%
import pandas as pd
import numpy as np
import math
import copy
import time
import os
import QSTK.qstkutil.qsdateutil as du
import datetime as dt
import QSTK.qstkutil.DataAccess as da
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkstudy.EventProfiler as ep
import matplotlib.pyplot as plt
from pandas import DataFrame, read_csv, Series
import sys
from dateutil.parser import parse
from matplotlib.patches import Ellipse
import matplotlib
from matplotlib.pyplot import figure,show
import matplotlib.dates as md
import dateutil
from yahoo_finance import Share

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

# Use data from 2010 to 2012 to find optimal portfolios
Adj_Close_Train = Adj_Close_2010_2012[tickers]

opt_data = Adj_Close_Train.values.copy() #Create NumPy array
tsu.returnize0(opt_data) # Normalize with respect to first value

# Get average returns, upper and lower bounds
(opt_avgrets, opt_std, b_error) = tsu.OptPort(opt_data, None)
opt_lower = np.zeros(opt_data.shape[1])
opt_upper = np.ones(opt_data.shape[1])
(f_min, f_max) = tsu.getRetRange(opt_data, opt_lower, opt_upper,opt_avgrets, s_type="long")

#%% Create optimal portfolios based on target return for all periods
k = [0.5,0.6,0.7,0.8,0.9,1.0]
portfolios = []
portfolios_std = []
optimal_tickers = []
for i in range(len(k)):
    target_return = k[i] * f_max
    (opt_weights, f_std, b_error) = tsu.OptPort(opt_data, target_return,opt_lower, opt_upper, s_type="long")
    opt_weights[opt_weights < 0.001] = 0.0 # Remove any tiny values
    portfolios.append(opt_weights)
    portfolios_std.append(f_std)
    t = list(np.array(opt_weights.nonzero()[0],dtype=int)) # Indexes of nonzero tickers
    for j in t:
        optimal_tickers.append(tickers[j]) #

optimal_tickers = list(set(optimal_tickers)) # These are the best companies to invest in

#%% USE BOLLINGER BAND ALGORITHM ON THIS OPTIMAL PORTFOLIO

Adj_Close_Test = Adj_Close_2013_2015[optimal_tickers]
dates_ALL = Adj_Close_Test.index
prices_ALL = Adj_Close_Test.values.copy()

# CALCULATE MOVING AVERAGE, MOVING STD AND BOLLINGER BANDS
wind_size = 20 # Size of window
k = 2.0 # Distance of Bollinger bands from moving average in number of STD

moving_avg = pd.rolling_mean(Adj_Close_Test,wind_size)
moving_std = pd.rolling_std(Adj_Close_Test,wind_size)
bollinger_up = moving_avg + (k * moving_std)
bollinger_down = moving_avg - (k * moving_std)

bollinger_values = (Adj_Close_Test - moving_avg)/moving_std

# GENERATE TRADING ORDERS ACCORDING TO SIGNALS

# Initialize orders list
orders = []
cash_to_spend = 1000.0

for s in optimal_tickers: # For all tickers
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
            Q = np.int(np.round(cash_to_spend / Adj_Close_Test[s][d]))
            order = y + ',' + m + ',' + da + ',' + str(s) + ',' + 'Buy,' + str(Q)
            orders.append(order)
            have_stocks = 'yes'
            bol = 'down'
        
        elif bollinger_values[s][d] > -k and bollinger_values[s][d] < k and Adj_Close_Test[s][d] >= moving_avg[s][d] and have_stocks == 'yes' and bol == 'down': # If you cross the mean line upwards
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
        
        elif bollinger_values[s][d] < k and bollinger_values[s][d] > -k and Adj_Close_Test[s][d] <= moving_avg[s][d] and have_stocks == 'no' and bol == '': # If you cross the mean line downwards
            #Generate Buy order
            y = str(int(date[0]))
            m = str(int(date[1]))
            da = str(int(date[2]))
            Q = np.int(np.round(cash_to_spend / Adj_Close_Test[s][d]))
            order = y + ',' + m + ',' + da + ',' + str(s) + ',' + 'Buy,' + str(Q)
            orders.append(order)
            have_stocks = 'yes'
            bol = 'up'
            
        else:
            continue

#%% Write CSV file
os.chdir(location)
filename = 'TS_optimized_bollinger_SP500_orders.csv'
f = open(filename,'w')
for line in orders:
    f.write(line)
    f.write('\n')
f.close()
