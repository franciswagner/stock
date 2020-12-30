import sqlite3
import pandas as pd
import yfinance as yf

conn = sqlite3.connect('dw_stock_data')

items = ['BIDI4.SA']

stock_data = yf.download(items,
                        period='1d',
                        interval='15m',
                        group_by='ticker')

stock_data.to_sql(name='tabela_cotacoes_mensal',con=conn, if_exists='replace')

table = pd.read_sql_query("""
    select * from tabela_cotacoes_mensal
""", conn)

print(table.tail(50))