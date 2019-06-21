
from instrument import Equity
from historical import HistoricalData, Distribution, Shock
from environment import Environment, FX, Price

import pandas as pd
from datetime import datetime

# Remove useless rows from CSVs
# Rewrite column names in ETF_price_data.csv to remove '/r'
full_info = pd.read_csv('data/ETF_info.csv')
df_prices = pd.read_csv('data/ETF_price_data.csv')
df_fx = pd.read_csv('data/USDCAD_data.csv')

ETF_list = list(df_prices.columns[1:])
ETF_count = len(ETF_list)
ETF_info = pd.DataFrame({'Ticker': ETF_list})
ETF_info = pd.merge(ETF_info, df_full_info, on='Ticker', how='left')

sectors = list(ETF_info['Fund Industry Focus'].unique())
regions = list(ETF_info['Fund Geographical Focus'].unique())

ETFs = []
for etf in ETF_list:
    ETFs.append(Equity(etf, 'USD'))

list_of_environments = []
dates = list(df_prices['Dates'])
num_dates = len(dates)
for i in range(num_dates):
    fx_row = df_fx.loc[i]
    date = datetime.strptime(dates[i],'%m/%d/%y')
    fx = FX('USD', fx_row['PX_MID'])
    
    market_prices = df_prices.loc[i]
    prices = []
    for etf in ETFs:
        price = market_prices[etf.name]
        prices.append(Price(etf, price))
    
    assert(fx_row['Dates'] == dates[i])
    assert(market_prices['Dates'] == dates[i])
    
    list_of_environments.append(Environment(date, prices, fx))

hist = HistoricalData(list_of_environments)