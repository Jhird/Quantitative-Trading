# -*- coding: utf-8 -*-
"""
Created on Tue Dec 08 22:32:31 2015

@author: Jahir Gutierrez

This file creates CSV files with financial data in the IBB index
- Open
- Close
- Adjusted Close
- Volume
- High
- Low

DESCRIPTION
Python Script that must be run from command line
-example-
python gethistoricaldata.py 2013

Inputs:
    -[0] name of this script (gethistoricaldata.py)
    -[1] year to extract data from (2013)

Output:
    - Six CSV files with historical data for all stocks in IBB
"""

#%% READ PACKAGES
import pandas as pd
from pandas import DataFrame, Series
import os
import sys
from yahoo_finance import Share
################################# IBB ########################################
#%% READ SYMBOLS AND ALLOCATIONS from IBB
location = os.getcwd()
os.chdir(location)
f = open('IBB_tickers.txt','r')
tickers = f.read().splitlines()
f.close()

year = '2010'
#year =  str(sys.argv[1])#Select year here
# GET INITIAL VALUES
startdate = year + '-01-01'
enddate = year + '-12-31'

symbols = []
historical_data = []

# Reference valuesfrom IBB index
ibb = Share('IBB')
historical_ibb = ibb.get_historical(startdate,enddate)
trading_days = len(historical_ibb)
init_date = historical_ibb[-1]['Date']
init_date = init_date.split('-')

for t in tickers:
    s = Share(t)
    h = s.get_historical(startdate,enddate)
    if len(h) != trading_days:
        continue
    else:
        historical_data.append(h)
        symbols.append(s.symbol)

historical_data.append(historical_ibb) # The IBB index will be the last column
symbols.append('IBB')

#%% MAKE QSTK COMPATIBLE DATAFRAMES
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
trading_dates = makeListOfDates(historical_ibb)
time_stamps = []
for date in trading_dates:
    time_stamps.append(pd.tslib.Timestamp(date + ' 16:00:00')) 
    
# Create Dataframes for a specific Key for all stocks
def makeDataFrameFromYFkey(yahooF_key):
    data = {} 
    for i in range(len(symbols)):
        l = makeListFromYFkey(historical_data[i],yahooF_key)
        data[symbols[i]] = Series(l, index=time_stamps)
    df = DataFrame(data)
    return df.sort_index()

# Create Dictionary of DataFrames as required by QSTK
list_dataframes = []
for k in yahooF_keys:
    list_dataframes.append(makeDataFrameFromYFkey(k))


#Change directory to IBB_historical
data_location = location + "\\IBB_historical"
os.chdir(data_location)
# This is the final data you can use with the QSTK library
qstk_data = dict(zip(yahooF_keys,list_dataframes))
for s_key in yahooF_keys:
    qstk_data[s_key] = qstk_data[s_key].fillna(method='ffill')
    qstk_data[s_key] = qstk_data[s_key].fillna(method='bfill')
    qstk_data[s_key] = qstk_data[s_key].fillna(1.0)
    df = qstk_data[s_key]
    filename = s_key + '_IBB_' + year + '.csv' 
    df.to_csv(filename)

###################### SP500 #################################################

"""
#%% READ PACKAGES
import urllib2
import datetime as dt
from bs4 import BeautifulSoup
import time
from yahoo_finance import Share

#%% GET ALL TICKERS IN SP500


SITE = "http://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

def scrape_list(site):
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = urllib2.Request(site, headers=hdr)
    page = urllib2.urlopen(req)
    soup = BeautifulSoup(page)

    table = soup.find('table', {'class': 'wikitable sortable'})
    sector_tickers = dict()
    for row in table.findAll('tr'):
        col = row.findAll('td')
        if len(col) > 0:
            sector = str(col[3].string.strip()).lower().replace(' ', '_')
            ticker = str(col[0].string.strip())
            if sector not in sector_tickers:
                sector_tickers[sector] = list()
            sector_tickers[sector].append(ticker)
    return sector_tickers

sector_tickers = scrape_list(SITE)
sector_names = sector_tickers.keys()
ls_symbols = []
for sector in sector_names:
    for ticker in sector_tickers[sector]:
        ls_symbols.append(ticker)

ls_symbols.sort()

#%% Make dataframes compatible with QSTK
tickers = ls_symbols

startdate = str(dt.datetime(2015,1,1))
enddate = str(dt.datetime(2015,12,31))
today = time.strftime("%Y-%m-%d")

startdate = startdate.replace(" 00:00:00","")

enddate = enddate.replace(" 00:00:00","")

stocks = []
for ticker in tickers:
    stocks.append(Share(ticker))

historical_data = []
for stock in stocks:
    if stock.get_historical(startdate,enddate) == []:
        continue
    else:
        historical_data.append(stock.get_historical(startdate,enddate))
        tickers.append(stock.symbol)

yahooF_keys = ['Adj_Close','Close','High','Low','Open','Volume']
"""