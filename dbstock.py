import sqlite3
import random

#versao 1.2 (multiplos usuarios; retorna todos os compromissos anotados)
#capaz de receber a data do compromisso em dia/mes/hora
#(deletar arquivo .db ou criar novo ao alterar colunas!!!)

class DBHelper:
    'Class that handles the SQL injection for the agenda function, including appoints, to dos and insights in the same database file'
    def __init__(self, dbagenda="dw_stock_data"): #creates a file agendatodo.sqlite
        self.dbagenda = dbagenda
        self.conn = sqlite3.connect(dbagenda)

    def setup_stocklist(self):
        stmt = "CREATE TABLE IF NOT EXISTS stocklist (description text, owner text)"
        self.conn.execute(stmt)
        self.conn.commit()


    def add_item(self, item_text, owner):
        stmt = "INSERT INTO stocklist (description, owner) VALUES (?, ?)"
        args = (item_text, owner)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_item(self, item_text, owner):
        stmt = "DELETE FROM stocklist WHERE description = (?) AND owner = (?)"
        args = (item_text, owner)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_items(self, owner):
        stmt = "SELECT description FROM stocklist WHERE owner = (?)"
        args = (owner, )
        return [x[0] for x in self.conn.execute(stmt, args)]
