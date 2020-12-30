
#%%

import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import sqlite3
import re
import datetime
from sqlalchemy import create_engine


conn = sqlite3.connect('dw_stock_data')

stock_names = ["EMBR3.SA",
            #    "BIDI3.SA",
            #    "CIEL3.SA",
            #    "ITSA4.SA",
            #    "MRFG3.SA",
            #    "ABEV3.SA",
            #    "CSNA3.SA",
               "GOAU3.SA"
               ]

stock_data = yf.download(stock_names,
                         period='2d',
                         interval='5m',
                         group_by='ticker'
                         ).round(2)

stock = 'EMBR3.SA'
stock_data[stock+'variation'] = stock_data['EMBR3.SA']['Open']-stock_data['EMBR3.SA']['Close']

index_column = [i for i in range(len(stock_data.index))]

stock_data2 = stock_data.set_index(pd.Index(index_column))
stock_data2['datetime'] = stock_data.index.strftime('%H:%M')


# print(stock_data2.loc[1,('datetime')].astype(str))

# line = str(stock_data2.loc[1,('datetime')].astype(str)) + str(stock_data2.loc[1,('EMBR3.SA','Open')])


# print(line)
# print(stock_data2.tail(2))
# print(stock_data2.loc[1,('EMBR3.SA')].to_string())

column_array_stock = stock_data.loc[:,('EMBR3.SA','Close')].values
# #qui precisa converter o objeto de data numpy para um objeto de data normal
column_array = stock_data.index.values.astype(str)

column_array2 = [datetime.datetime.strptime(i[:16],"%Y-%m-%dT%H:%M") for i in column_array]

# for i in range(len(column_array)):
#     print(column_array2[i],column_array_stock[i])

# print(stock_data['EMBR3.SA']['Close'])
# print(stock_data.head(10))
# print(stock_data.loc[,('EMBR3.SA','Close')])



# stock_data.to_sql(name='tabela_cotacoes_mensal',con=conn, if_exists='replace')


stocks = pd.read_sql_query('select * from tabela_cotacoes_mensal limit 50', con=conn).round(2)

# columns = stocks.columns
# new_columns = []


# for i in range(len(columns)):
#     new_columns.append(re.sub(r"(\'|\(|\)|,|\s|SA)",r"",re.sub(r"\.","_",columns[i])))

# def rename(column):
#     new_column = re.sub(r"(\'|\(|\)|,|\s|sa)",r"",re.sub(r"\.","_",column.lower()))
#     return new_column

# stocks = stocks.rename(columns=rename)


# print(stocks.)

# print(stocks.head(10))

# db_tests = pd.DataFrame(data=stocks[['datetime','bidi3_open','bidi3_close']], index=stocks.index)
# db_tests['variation'] = db_tests['bidi3_open']-db_tests['bidi3_close']


# quantile_1 = db_tests.quantile(q=0.25,axis='index')
# quantile_4 = db_tests.quantile(q=0.75,axis='index')

# print(quantile_1['variation'],quantile_4['variation'])

# def f1(x):
#     if db_tests.iloc[x.name]['variation'] < quantile_1['variation']:
#         return 'fall_25'
#     elif db_tests.iloc[x.name]['variation'] > quantile_4['variation']:
#         return 'rise_25'
#     else:
#         return 'average'

# db_tests['variation_degree'] = db_tests.apply(f1, axis=1)

# print(db_tests.head(10))

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


# stocks['slopes'] = pd.DataFrame(data=stocks['Close'].rolling(5, center=True, win_type='nuttall').mean(), 
#                            index=stocks.index)
# # stocks['accumulated_delta'] = stocks['Close']


# stocks['diff'] = stocks['slopes'].diff()

stocks['label'] = stocks.apply(f, axis=1)
# stocks['Datetime2'] = pd.to_datetime(stocks['Datetime'], errors='coerce').dt.date

print(stocks.head(10))


# plt.plot(stocks.index, stocks['Close'],stocks['slopes'])

# plt.show()


# plt.savefig('/home/yuguro/Desktop/py_envs/stock_project/teste.png')

# print(stocks.head(50))


# %%
