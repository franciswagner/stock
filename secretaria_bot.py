from dbhelperfull import DBHelper

#version 1.0

import json      #modulo que faz comunicacao com o python
import requests
import time
import urllib #lida com caracteres especi


#global variables
TOKEN = "503202014:AAESDWPkUBqiwkQm_rLI90FtsGlyn3RStQk"
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
    t1 = time.clock()
    while True:
        t2 = time.clock()
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
        print("agora sei lidar com mais de 1 mensagem")
        for update in updates["result"]:
            content = []
            if 'text' in update["message"]:#checa se existe a key 'text' no dict
                content.append(str(update["message"]["text"]))
            else:
                print("nao sei lidar com updates q nao sao textos ainda :(")
                continue
        return
    elif num_updates == 1:
        text = "Diga o que vc deseja:"
        options = ["To do","Agenda","Checar Anotações Raw","Gastos"]
        keyboard = build_keyboard(options)
        send_message(text,chat,keyboard)
        last_update_id = get_last_update_id(updates) + 1
        updates = get_updates(last_update_id)
        try:
            if updates["result"][0]["message"]["text"] == "Agenda":
                last_update_id = get_appoints(updates, chat)
                return last_update_id
        except:
            return
            print("disistiu do compromisso?")

        try:
            if updates["result"][0]["message"]["text"] == "To do":
                last_update_id = get_todos(updates, chat)
                return last_update_id
        except:
            return

        try:
            if updates["result"][0]["message"]["text"] == "Checar Anotações Raw":
                last_update_id = get_raw(updates, chat)
                return last_update_id
        except:
            return
            print('vc desistiu de anotar?')

        try:
            if updates["result"][0]["message"]["text"] == "Gastos":
                last_update_id = cash_flow(updates,chat)
                return last_update_id
        except:
            return
            print('Desistiu...')
        if updates["result"][0]["message"]["text"] == "Treinar" or updates["result"][0]["message"]["text"] == "treinar":
            last_update_id = treinar(updates, chat)
        elif updates["result"][0]["message"]["text"] == "Ver":
            last_update_id = ver(updates,chat)
        elif updates["result"][0]["message"]["text"] == "Importante":
            importante(updates,chat)
        elif (updates["result"][0]["message"]["text"]).upper() == "APAGAR":
            remove_raw(updates,chat)
        elif (updates["result"][0]["message"]["text"]).upper() == "TESTE":
            testes(chat,updates)
        elif (updates["result"][0]["message"]["text"]).upper() == "QUERY":
            custom_query(chat,updates)
        else:
            try:
                text = updates["result"][0]["message"]["text"]
                last_update_id = raw_input(updates,text,chat)
                return last_update_id
            except:
                return
    return


def get_appoints(updates, chat):
    Flag = True
    while Flag == True:
        options = ["Novo", "Ver", "Pronto"]
        text = "Diga o que você quer: 'Novo' para adicionar novo compromisso ou 'Ver' para ver a agenda (Digite 'Pronto' para sair)"
        keyboard = build_keyboard(options)
        send_message(text,chat,keyboard)
        last_update_id = get_last_update_id(updates) + 1
        updates = get_updates(last_update_id)
        if len(updates["result"]) == 0:
            return last_update_id
        if updates["result"][0]["message"]["text"] == 'Pronto':
            Flag = False
            return last_update_id
        elif updates["result"][0]["message"]["text"] == 'Novo':
            send_message("Digite a descricao do seu compromisso: ",chat)
#            while updates["result"][0]["message"]["chat"]["id"] != chat: #lidar com msgs atravessadas!!!
#               last_update_id = get_last_update_id(updates) + 1
#               updates = get_updates(last_update_id)
            last_update_id = get_last_update_id(updates) + 1
            updates = get_updates(last_update_id)
            description = updates["result"][0]["message"]["text"]
            send_message("Digite em que mês (numero inteiro) será seu compromisso: ",chat)
            last_update_id = get_last_update_id(updates) + 1
            updates = get_updates(last_update_id)
            date_mes = updates["result"][0]["message"]["text"]
            send_message("Digite o dia do mês em que será seu compromisso: ",chat)
            last_update_id = get_last_update_id(updates) + 1
            updates = get_updates(last_update_id)
            date_dia = updates["result"][0]["message"]["text"]
            send_message("Digite a hora do seu compromisso: (apenas valor inteiro)",chat)
            last_update_id = get_last_update_id(updates) + 1
            updates = get_updates(last_update_id)
            date_hora = updates["result"][0]["message"]["text"]
            db.add_appoint(description, date_mes, date_dia, date_hora, chat)
        elif updates["result"][0]["message"]["text"] == "Ver":
            items = db.see_appoint(chat)
            lines = []
            for description,date_dia,date_hora in zip(items['description'], items['date_dia'], items['date_hora']):
                line = description + ' --> dia ' + str(date_dia) + ' às ' + str(date_hora) + ' horas '
                lines.append(line)
            message = formating2(lines)
            send_message(message, chat)


def get_todos(updates, chat):
    while True:
        items = db.get_items(chat)
        options = ['Ver','Pronto']
        keyboard = build_keyboard(options)
        send_message("Diga o que você quer: 'Ver' para ver a lista e checar items feitos ou digite o novo item (Digite 'Pronto' para sair)",chat,keyboard)
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
                db.delete_item(text, chat)
                continue
        else:
            db.add_item(text, chat)
            items = db.get_items(chat)
            message = formating2(items)
            send_message(message, chat)


def raw_input(updates,content,chat):
    word_list = db.check_raw(chat)
    located_words = set(content.split()) & set(word_list)
    all_words = set(content.split())
    reminder_words = ['relembrar','importante','Relembrar','Importante']
    if bool(set(reminder_words) & set(all_words)):
        reminder_flag = 1
    else:
        reminder_flag = 0
    if located_words: #caso o conjunto seja não vazio o valor será verdadeiro
        text = "Deseja adicionar essa anotação em alguma dessas categorias? \n" + formating2(located_words)
        items = ["Sim","Não","Voltar"]
        keyboard = build_keyboard(items)
        send_message(text,chat,keyboard)
        last_update_id = get_last_update_id(updates) + 1
        updates = get_updates(last_update_id)
        text = updates["result"][0]["message"]["text"]
        if text == "Sim":
            text = "Escolha a categoria dentre as categorias sugeridas: \n" + formating2(located_words)
            keyboard = build_keyboard(list(located_words))
            send_message(text,chat,keyboard)
            last_update_id = get_last_update_id(updates) + 1
            updates = get_updates(last_update_id)
            column = updates["result"][0]["message"]["text"]
            db.add_raw(column,content,chat,reminder_flag)
        elif text == "Não":
            text = "Digite uma palavra para representar essa nova categoria: "
            send_message(text,chat)
            last_update_id = get_last_update_id(updates) + 1
            updates = get_updates(last_update_id)
            if len(updates["result"]) == 0:
                return last_update_id
            text = updates["result"][0]["message"]["text"]
            db.add_raw(column,content,chat,reminder_flag)
    else:
        text = 'Não foi encontrada uma palavra chave na sua anotação, digite uma palavra para ser o rótulo dessa anotação:'
        items = ["Voltar"]
        keyboard = build_keyboard(items)
        send_message(text,chat,keyboard)
        last_update_id = get_last_update_id(updates) + 1
        updates = get_updates(last_update_id)
        if len(updates["result"]) == 0:
            return last_update_id
        word = updates["result"][0]["message"]["text"]
        if word == "Voltar":
            return last_update_id
        else:
            categories = db.check_raw(chat)
            if word not in categories:
                db.add_raw(word,content,chat,reminder_flag)
            else:
                text = 'Já existe uma categoria com esse nome. Digite novamente e no início da frase a palavra coloque a palavra ' + word
                send_message(text,chat)
    return last_update_id


def get_raw(updates,chat):
    try:
        items = db.check_raw(chat)
        text = "Qual categoria você deseja ver?"
        keyboard = build_keyboard(items)
        send_message(text,chat,keyboard)
        last_update_id = get_last_update_id(updates) + 1
        updates = get_updates(last_update_id)
        if len(updates["result"]) == 0:
            return
        column = updates["result"][0]["message"]["text"]
        notes = db.get_raw(chat,column)
        formating(notes,chat)
    except:
        warn = "Não há nenhuma categoria de anotação ainda."
        send_message(warn,chat)
    return


def remove_raw(updates,chat):
    items = db.check_raw(chat)
    text = "Qual categoria você deseja apagar?"
    keyboard = build_keyboard(items)
    send_message(text,chat,keyboard)
    last_update_id = get_last_update_id(updates) + 1
    updates = get_updates(last_update_id)
    if len(updates["result"]) == 0:
        return
    column = updates["result"][0]["message"]["text"]
    notes = db.get_raw(chat,column)
    keyboard = build_keyboard(notes)
    formating(notes,chat,keyboard)
    last_update_id = get_last_update_id(updates) + 1
    updates = get_updates(last_update_id)
    if len(updates["result"]) == 0:
        return
    else:
        text = updates["result"][0]["message"]["text"]
        db.remove_raw(column,text,chat)
    return


def importante(updates,chat):
    items = db.get_reminder_raw(chat,1)
    text = "Essas são as anotações importantes que você possui: \n" + formating2(items)
    send_message(text,chat)


def treinar(updates,chat):
    words = db.select_words()
    text = "Digite frases quaisquer e depois explique o significado das palavras e da frase."
    send_message(text,chat)
    last_update_id = get_last_update_id(updates) + 1
    updates = get_updates(last_update_id)
    content = updates["result"][0]["message"]["text"]
    content = set(content.split())
    content = (x for x in content if x not in words)
    for i in content:
        text = "Qual a classe dessa palavra?" + i + "\n - noun (n) \n - pronoun (p) \n - article (a) \n - verb (v) \n - adjective (a) \n - preposition (pr) \n - conjunction (c)"
        send_message(text,chat)
        last_update_id = get_last_update_id(updates) + 1
        updates = get_updates(last_update_id)
        try:
            word_class = updates["result"][0]["message"]["text"]
        except:
            return
        db.insert_words(i,word_class)
    return last_update_id


def ver(updates,chat):
    words = db.select_words()
    text = "Essas são as palavras que você possui na base: \n" + formating2(words)
    send_message(text,chat)
    return


def cash_flow(updates,chat):
    options = ["Novo gasto","Ver gasto mensal","Ver lista de gastos","Ver gasto por categoria (mensal)"]
    text = "Diga o que você deseja:"
    keyboard = build_keyboard(options)
    send_message(text,chat,keyboard)
    last_update_id = get_last_update_id(updates) + 1
    updates = get_updates(last_update_id)
    pick = updates["result"][0]["message"]["text"]
    if pick == "Novo gasto":
        text = "Diga o tipo de gasto que você teve: (comida,mercado,etc...)"
        send_message(text,chat)
        last_update_id = get_last_update_id(updates) + 1
        updates = get_updates(last_update_id)
        label = updates["result"][0]["message"]["text"]
        text = "Descreva com o que foi o gasto:"
        send_message(text,chat)
        last_update_id = get_last_update_id(updates) + 1
        updates = get_updates(last_update_id)
        description = str(updates["result"][0]["message"]["text"])
        text = "Quanto você gastou?"
        send_message(text,chat)
        last_update_id = get_last_update_id(updates) + 1
        updates = get_updates(last_update_id)
        ammount = float(updates["result"][0]["message"]["text"])
        db.accounting_insert(chat,ammount,label,description)
    if pick == "Ver gasto mensal":
        try:
            print('entrou no check')
            periods = db.accounting_check_periods(chat)
        except:
            text = 'Erro! Talvez não haja nenhum gasto registrado ainda.'
            send_message(text,chat)
        text = 'Esses são os meses em que você possui gastos: '
        keyboard = build_keyboard(periods)
        send_message(text,chat,keyboard)
        last_update_id = get_last_update_id(updates) + 1
        updates = get_updates(last_update_id)
        period = updates["result"][0]["message"]["text"]
        items = db.accounting_select(chat,period)
        lines = []
        for period,ammount in zip(items['periods'], items['ammounts']):
            line = str(period) + ' --> ' + str(ammount)
            lines.append(line)
        message = formating2(lines)
        send_message(message,chat)
    if pick == "Ver gasto por categoria (mensal)":
        try:
            periods = db.accounting_check_periods(chat)
        except:
            text = 'Erro! Talvez não haja nenhum gasto registrado ainda.'
            send_message(text,chat)
        text = 'Esses são os meses que você possui gastos: '
        keyboard = build_keyboard(periods)
        send_message(text,chat,keyboard)
        last_update_id = get_last_update_id(updates) + 1
        updates = get_updates(last_update_id)
        period = updates["result"][0]["message"]["text"]
        text = 'Essas são as categorias em que você possui gastos em ' + str(period)
        cats = db.accounting_check_cats(chat,period)
        print(cats)
        keyboard = build_keyboard(cats)
        send_message(text,chat,keyboard)
        last_update_id = get_last_update_id(updates) + 1
        updates = get_updates(last_update_id)
        category = updates["result"][0]["message"]["text"]
        items = db.accounting_select(chat,period,category)
        lines = []
        for period,ammount,category in zip(items['periods'], items['categories'], items['ammounts']):
            line = str(period) + ' : ' + str(category) + ' --> ' + str(ammount)
            lines.append(line)
        message = formating2(lines)
        send_message(message,chat)
    elif pick == "Ver lista de gastos":
        items = db.accounting_select(chat)
        lines = []
        for category,ammount,date,detail in zip(items['categories'],items['ammounts'],items['dates'],items['details']):
            line = category + ' --> R$' + str(ammount) + ' em ' + str(date) + ' (' + detail + ')'
            lines.append(line)
        formating(lines,chat)
    return last_update_id


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


def monitoring():
    time_struct = time.localtime()
    min_atual = time_struct[4]
    hora_atual = time_struct[3] - 3
    if hora_atual < 0:
        hora_atual = 24 + hora_atual
    dia_atual = time_struct[2]
    mes_atual = time_struct[1]
    # for handling agenda
    contents = db.get_all()
    for content in contents:
        for thing,mes,dia,hora in zip(content['description'], content['mes'],content['dia'],content['hora']):
            if type(mes) is not int:
                mes = mes_atual
                text = 'O mes precisa ser digitado em formato de número (ex. abril = 4)'
                send_message(text,content['id'])
                db.delete_appoint_fast(thing,content['id'])
                continue
            if type(dia) is not int:
                dia = dia_atual
                text = 'Tem certeza que você digitou certo? Era pra digitar um número representando o dia do mês (1-31).'
                send_message(text,content['id'])
                db.delete_appoint_fast(thing,content['id'])
                continue
            else:
                if dia < dia_atual and mes <= mes_atual: #deleta
                    db.delete_appoint(thing,mes,dia,hora,content['id'])
                    continue
                if dia == dia_atual + 1 and mes == mes_atual and hora_atual == 23 and min_atual < 5:
                    line = '--> ' + thing + ' <-- amanhã às:' + str(hora)
                    send_message(line, content['id'])
                    continue
                if dia == dia_atual and mes == mes_atual: #lembra
                    if type(hora) is not int:
                        db.delete_appoint(thing,mes,dia,hora,content['id'])
                        text = 'Compromisso ' + thing + 'concluído.' + '\n ' + 'Escreva a data em numero inteiro na proxima vez'
                        send_message(text, content['id'])
                        continue
                    elif hora_atual > hora - 2:
                        line = '--> ' + thing + ' <-- às:' + str(hora)
                        send_message(line, content['id']) #freq de envio (!)
                        db.delete_appoint(thing,mes,dia,hora,content['id'])
                        continue
                if dia > dia_atual:
                    continue
    return


    # for handling reminders in the raw content, especially set times for the rememberings
    # if hora_atual == 9 or hora_atual == 12 or hora_atual == 15 and min_atual > 0 and min_atual < 9:
    #     db.ed_remember()


    # if hora_atual == 8 and (10 == min_atual + 4 or 10 == min_atual - 4):
    #     infos = db.get_ed_remember()

    # try:
    #     for id_test,owner,category,hour,minute in zip(infos['id_tests'],infos['owners'],infos['categories'],infos['hours'],infos['minutes']):
    #         if hour == hora_atual and (minute == min_atual + 4 or minute == min_atual - 4):
    #             notes = db.get_reminder_raw(category,owner,1)
    #             text = "Essa é uma das paradas que você pediu para ser lembrado: \n" + formating(notes)
    #             send_message(text,owner)
    #             return
    #         else:
    #             continue
    # except:
    #     print('ainda nao entou em infos')
    #     return



def testes(chat,updates):

    keyboard = [[{"text": "texto1","request_location": True}]]
    reply = {"keyboard":keyboard, "one_time_keyboard": True}
    reply_markup = json.dumps(reply)
    send_message("Responda algo",chat,reply_markup)
    last_update_id = get_last_update_id(updates) + 1
    updates = get_updates(last_update_id)
    print(get_updates(last_update_id-1))
    location = updates["result"][0]["message"]["location"]
    print(location)
    send_message("Essa é a sua localizacao em coordenadas:" + str(location["latitude"]) + ' ' + str(location["longitude"]),chat)
    return

def custom_query(chat_id,updates):
    send_message("Mande a sua query para o banco executar (apenas uma coluna)",chat_id)

    last_update_id = get_last_update_id(updates) + 1
    updates = get_updates(last_update_id)
    query = updates["result"][0]["message"]["text"]
    things = db.custom_query(chat_id,query)

    print(things)

    try:
        formating(things,chat_id)
    except:
        send_message('falhou em mandar a mensagem',chat_id)



def main():
    length = 0
    db.setup_agenda()
    db.setup_todolist()
    db.create_raw_table()
    db.create_word()
    db.create_accounting_table()
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
        if time_abs_now > time_abs_ref + interval:
            monitoring()
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
