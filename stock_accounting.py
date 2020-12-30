
import pandas as pd
import datetime
import sqlite3

filepath = "//home//yuguro//Downloads//notas_corretagem.csv"

conn = sqlite3.connect('dbstocks')

def prepare_table():
    table = pd.read_csv(filepath, usecols=['date', 'qtd', 'titulo', 'compra', 'venda','inter_taxas'])

    for i in table.index:
        table.loc[i,"date"] = datetime.datetime.strptime(table.loc[i,"date"], "%Y-%m-%d")
    return table


def query_month_total():
    table = pd.read_sql_query("""
        select  substr(date,1,4)||substr(date,6,2) as anomes,
                sum(case when compra*1 > 0 then qtd else 0 end) as qtd_bought,
                sum(case when venda*1 > 0 then qtd else 0 end) as qtd_sold,
                sum(qtd*ifnull(compra,0)) as bought,
                sum(qtd*ifnull(venda,0)) as sold,
                sum(ifnull(inter_taxas,0)) as taxas
        from notas_corretagem
        group by 1
    """,conn)
    return table


def query_daytrade_resultado():
    table = pd.read_sql_query("""
        select  substr(date,1,4)||substr(date,6,2) as anomes,
                sum(resultado) as resultado
        from(
            select  date,
                    titulo,
                    sum(case when compra*1 > 0 then qtd else 0 end) as qtd_compra,
                        sum(case when venda*1 > 0 then qtd else 0 end) as qtd_venda,
                        sum(case when compra*1 > 0 then compra*1*qtd else 0 end) as compra,
                        sum(case when venda*1 > 0 then venda*1*qtd else 0 end) as venda,
                        sum(ifnull(inter_taxas,0)) as taxas,
                    sum(case when compra*1 > 0 and venda*1 > 0 then venda*1*qtd - compra*1*qtd else 0 end) as resultado
            from notas_corretagem
            group by date,
                    titulo
        )
        group by 1
    """,conn)
    return table

def query_swingtrade_resultado():
    table = pd.read_sql_query("""
    with
    base_daytrade as (
        select date,
            titulo,
            sum(case when compra*1 > 0 then qtd else 0 end) as qtd_compra,
                sum(case when venda*1 > 0 then qtd else 0 end) as qtd_venda,
                sum(case when compra*1 > 0 then compra*1*qtd else 0 end) as compra,
                sum(case when venda*1 > 0 then venda*1*qtd else 0 end) as venda,
                sum(ifnull(inter_taxas,0)) as taxas,
            sum(case when compra*1 > 0 and venda*1 > 0 then venda*1*qtd - compra*1*qtd else 0 end) as resultado
        from notas_corretagem
        group by date,
                titulo),

    base_swingtrade as (
        select substr(date,1,4)||substr(date,6,2) as anomes,
            titulo,
            sum(qtd_compra) as qtd_compra2,
                sum(qtd_venda) as qtd_venda2,
                sum(compra) as compra,
                sum(venda) as venda,
                sum(taxas) as taxas
        from base_daytrade
        where qtd_compra > qtd_venda or qtd_compra < qtd_venda
        group by 1,2),
    
    base_overmonth as (
        SELECT  anomes,
                titulo,
                case when qtd_compra2 > qtd_venda2 then (qtd_compra2-qtd_venda2) else 0 end as qtd_compra,
                case when qtd_compra2 > qtd_venda2 then (qtd_compra2-qtd_venda2)*compra/qtd_compra2 else 0 end as compra,
                case when qtd_compra2 < qtd_venda2 then (qtd_venda2-qtd_compra2) else 0 end as qtd_venda,
                case when qtd_compra2 < qtd_venda2 then (qtd_venda2-qtd_compra2)*venda/qtd_venda2 else 0 end as venda
        from base_swingtrade),

    base_swingtrade_apurada as (
        select anomes,
            titulo,
            qtd_compra2,
            compra,
            case when qtd_compra2 = 0 then 0 else compra/qtd_compra2 end as preco_medio_compra,
            qtd_venda2,
            venda,
            case when qtd_venda2 = 0 then 0 else venda/qtd_venda2 end as preco_medio_venda,
            case when qtd_compra2 > 0 and qtd_venda2 > 0 then venda/qtd_venda2*min(qtd_venda2,qtd_compra2)-compra/qtd_compra2*min(qtd_venda2,qtd_compra2) end as resultado
        from base_swingtrade),

    base_overmonth_apurada as (
        select a.anomes_venda,
                a.titulo,
                a.qtd_venda,
                venda-compra as resultado
        from(
            select  titulo,
                    sum(qtd_venda) as qtd_venda,
                    max(anomes) as anomes_venda,
                    sum(venda) as venda
            from base_overmonth 
            where qtd_venda > 0 
            group by 1) a
        left join (
            select titulo,
                    anomes as anomes_compra,
                    sum(qtd_compra) as qtd_compra,
                    sum(compra) as compra
            from base_overmonth
            where qtd_compra > 0 
            group by 1,2) b
            on a.titulo = b.titulo and a.qtd_venda = b.qtd_compra
            --atencao aqui nessa etapa da logica, pode ter algum bug com acoes de mesmo titulo em meses diferentes!!!
        where anomes_venda > anomes_compra)

    select anomes,
            tipo,
            sum(ifnull(resultado,0)) as resultado
    from(
        select anomes,
                titulo,
                resultado,
                'intramonth' as tipo
        from base_swingtrade_apurada
        union all
        select anomes_venda as anomes,
                titulo,
                resultado,
                'overmonth' as tipo
        from base_overmonth_apurada)
    group by anomes,
            tipo
    """,conn)
    return table



def sql(table):
    # table.to_sql('notas_corretagem', con=conn, if_exists='replace')
    table = query_swingtrade_resultado()
    # table = query_daytrade_resultado()
    print(table.tail(40))

    # table.to_csv('table_stocks', index=False)

def main():
    table = prepare_table()
    sql(table)


if __name__ == "__main__":
    main()