
#%%

import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import sqlite3
import re
import datetime
from sqlalchemy import create_engine


conn = sqlite3.connect('dw_stock_data')


stocks = pd.read_sql_query('select * from tabela_cotacoes_mensal limit 50', con=conn).round(2)


def f(x):
    if x.name == 0 or x.name == len(stocks.index) -1:
        return
    if stocks.iloc[x.name-1]['Close'] > stocks.iloc[x.name]['Close'] < stocks.iloc[x.name+1]['Close']:
        return 'valley'
    elif stocks.iloc[x.name-1]['Close'] > stocks.iloc[x.name]['Close'] > stocks.iloc[x.name+1]['Close']:
        return 'fall'
    elif stocks.iloc[x.name-1]['Close'] < stocks.iloc[x.name]['Close'] > stocks.iloc[x.name+1]['Close']:
        return 'peak'
    elif stocks.iloc[x.name-1]['Close'] < stocks.iloc[x.name]['Close'] < stocks.iloc[x.name+1]['Close']:
        return 'rise'
    else:
        return 'flat'

stocks['label'] = stocks.apply(f, axis=1)

print(stocks.head(10))


# %%
