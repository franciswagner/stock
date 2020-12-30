#nocoes gerais:
# construir modelo para o intervalo medio de oscilacao e qual o comportamento dessa oscilacao:
# usar a taxa de crescimento medio da empresa (projecao linear usando fechamentos em periodos largos)
# ao redor dessa projecao, construir as oscilacoes medias


from dbstock import DBHelper

# bot pra monitorar precos e situacoes no mercado

import json      #modulo que faz comunicacao com o python
import requests
import time
import urllib #lida com caracteres especiais

import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import re

conn = sqlite3.connect('dw_stock_data')

plt.figure(figsize=(12,8))


#global variables
TOKEN = "977165415:AAEXEkUgbDiOoEkzXgxRlyicAvGad-MT6v4"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

emoji1 = u'\U000027A1'   #seta pra direita

db = DBHelper()

def get_url(url):
    try:
        response = requests.get(url)
    except:
        print("problema com o request")
        return
    content = response.content.decode("utf8")
    return content


#maneira de obter conteudo do telegram e converte-lo pra python
def get_json_from_url(url):
    content = get_url(url)
    try:
        js = json.loads(content)
    except:
        print("Deu pau no json")
        return
    return js


#offset trabalha com o numero sequencial das msgs, dar como argumento um update_id
#faz com que o update seja lido a partir daquela msg
def get_updates(offset=None):
    t1 = time.process_time()
    while True:
        t2 = time.process_time()
        url = URL + "getUpdates?timeout=100"
        if offset:
            url += "&offset={}".format(offset)
        js = get_json_from_url(url)
        if t2 - t1 > 0.02:
            return js
        try:
            if len(js["result"]) == 0:
                continue
        except:
            print('deu pau na leitura do json...')
            continue
        else:
            return js


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def general_handler(updates, num_updates, chat):
    if num_updates > 1:
        print('bla')
        # print("agora sei lidar com mais de 1 mensagem")
        # for update in updates["result"]:
        #     content = []
        #     if 'text' in update["message"]:#checa se existe a key 'text' no dict
        #         content.append(str(update["message"]["text"]))
        #     else:
        #         print("nao sei lidar com updates q nao sao textos ainda :(")
        #         continue
        # return
    elif num_updates == 1:
        text = "Diga o que vc deseja:"
        options = ["Setar Watchlist","Ver Graficos"]
        keyboard = build_keyboard(options)
        send_message(text,chat,keyboard)
        last_update_id = get_last_update_id(updates) + 1
        updates = get_updates(last_update_id)
        if updates["result"][0]["message"]["text"] == "Setar Watchlist":
            last_update_id = watchlist(updates, chat)
            return last_update_id
        elif updates["result"][0]["message"]["text"] == "Ver Graficos":
            last_update_id = get_charts(updates, chat)
            return last_update_id
    return


def watchlist(updates, chat):
    while True:
        items = db.get_items(chat)
        options = ['Ver','Pronto']
        keyboard = build_keyboard(options)
        send_message("Diga o que voce quer: 'Ver' para ver a lista e checar items feitos ou digite o novo item (Digite 'Pronto' para sair)",chat,keyboard)
        last_update_id = get_last_update_id(updates) + 1
        updates = get_updates(last_update_id)
        if len(updates["result"]) == 0:
            return last_update_id
        text = updates["result"][0]["message"]["text"]
        if text == 'pronto' or text == 'Pronto':
            return last_update_id
        elif text == "Ver":
            keyboard = build_keyboard(items)
            send_message("Check the items done", chat, keyboard)
            last_update_id = get_last_update_id(updates) + 1
            updates = get_updates(last_update_id)
            if len(updates["result"]) == 0:
                return last_update_id
            elif updates["result"][0]["message"]["text"] == 'pronto' or updates["result"][0]["message"]["text"] == 'Pronto':
                continue
            else:
                text = updates["result"][0]["message"]["text"]
                db.delete_item(text, chat, items)
                continue
        else:
            db.add_item(text, chat)
            items = db.get_items(chat)
            message = formating2(items)
            send_message(message, chat)

def update_stock_prices(updates, chat):
    items = db.get_items(chat)
    try:
        stock_data = yf.download(items,
                                period='1mo',
                                interval='15m',
                                group_by='ticker'
                                )
        stock_data.to_sql(name='tabela_cotacoes_mensal',con=conn, if_exists='replace')
    except:
        send_message('algum nome errado de acao',chat)


def get_charts(updates, chat):
    items = db.get_items(chat)
    stock_data_actual = yf.download(
        tickers = items,
        period = "1d",
        interval = "2m",
        group_by = "ticker"
    )

    stock = items[0]
    fig = go.Figure(data=[go.Candlestick(x=stock_data_actual.index,
                                        open=stock_data_actual[stock,'Open'],
                                        high=stock_data_actual[stock,'High'],
                                        low=stock_data_actual[stock,'Low'],
                                        close=stock_data_actual[stock,'Close']
                                        )
                         ]
                    )

    fig.write_image('/home/yuguro/Desktop/py_envs/stock_project/temp_chart1.png')
    send_image(chat)


def send_image(chat):
    files = {'photo': open('/home/yuguro/Desktop/py_envs/stock_project/temp_chart1.png','rb')}
    data = {'chat_id': chat}
    r = requests.post('https://api.telegram.org/bot977165415:AAEXEkUgbDiOoEkzXgxRlyicAvGad-MT6v4/sendPhoto',
                  files=files,
                  data = data)
    print(r.status_code,r.reason, r.content)

# files = {'photo': open('./saved/{}.jpg'.format(user_id), 'rb')}
# status = requests.post('https://api.telegram.org/bot<TOKEN>/sendPhoto?chat_id={}'.format(chat_id), files=files)

def send_message(text,chat_id,reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)

def formating2(text):
    content = ''
    for i in text:
        try:
            i = '\n' + emoji1 + i
        except:
            i = str(i)
            i = '\n' + emoji1 + i
        content = content + i
    return content

def formating(text,chat_id,reply_markup=None):
    content = ''
    len_total = 0
    limit = 3500
    i0 = 0
    for i in text:
        len_total = len_total + len(i)
    print(len_total)
    if len_total < limit:
        for i in text:
            if i:
                try:
                    i = '\n' + emoji1 + i
                except:
                    i = str(i)
                    i = '\n' + emoji1 + i
            content = content + i
        send_message(content,chat_id,reply_markup)
    elif len_total > limit:
        for i in text:
            if i:
                try:
                    i = '\n' + emoji1 + i
                except:
                    i = str(i)
                    i = '\n' + emoji1 + i
                content = content + i
        n = int(len_total/limit)
        print(content)
        while i0 <= n:
            i1 = i0 + 1
            partial_msg = content[i0*limit:i1*limit]
            send_message(partial_msg,chat_id,reply_markup)
            i0 = i1
    return


def build_keyboard(items):
    keyboard = [[str(item)] for item in items]
    reply_markup = {"keyboard":keyboard, "one_time_keyboard":True}
    return json.dumps(reply_markup)


def main():
    db.setup_stocklist()
    time_abs_ref = time.time() #secs since epoch
    last_update_id = None
    interval = 180.0 #[sec]
    while True:
        time_abs_now = time.time()
        updates = get_updates(last_update_id)
        try:
            length = len(updates["result"])
        except:
            print("Deu problema no update")
            return
        if time_abs_now > time_abs_ref + interval:
            # monitoring()
            time_abs_ref = time_abs_now
        if length > 0:
            try:
                chat = updates["result"][0]["message"]["chat"]["id"]
            except:
                chat = updates["result"][0]["edited_message"]["chat"]["id"]
            general_handler(updates, length, chat)
            last_update_id = get_last_update_id(updates) + 1
        else:
            time.sleep(0.5)
            continue

if __name__ == '__main__':
    main()
