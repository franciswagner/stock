with
base_trades as (
  	select date,
  		   titulo,
  		   sum(case when compra*1 > 0 then qtd else 0 end) as qtd_compra,
  			sum(case when venda*1 > 0 then qtd else 0 end) as qtd_venda,
  			sum(case when compra*1 > 0 then compra*1*qtd else 0 end) as compra,
  			sum(case when venda*1 > 0 then venda*1*qtd else 0 end) as venda,
  			sum(ifnull(inter_taxas,0)) as taxas,
  		   sum(case when compra*1 > 0 and venda*1 > 0 then venda*1*qtd - compra*1*qtd else 0 end) as resultado
  	from stocks.notas_corretagem
	--where date <= '2019-12-31'
	group by date,
			 titulo),

base_swingtrade as (
  	select 
        extract(year from date)||FORMAT("%02d",extract(month from date)) as anomes,
  		  titulo,
  		  sum(qtd_compra) as qtd_compra2,
  			sum(qtd_venda) as qtd_venda2,
  			sum(compra) as compra,
  			sum(venda) as venda,
  			sum(taxas) as taxas
  	from base_trades
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
    
base_overmonth_apurada as (
  select titulo,
          max(case when qtd_venda > 0 then anomes else null end) as anomes,
          sum(qtd_compra) as qtd_compra,
          sum(qtd_venda) as qtd_venda,
          sum(compra) as compra,
          sum(venda) as venda
  from base_overmonth
  group by 1
  ),

base_swingtrade_apurada as (
  	select anomes,
  		   titulo,
  		   qtd_compra2,
  		   compra,
  		   case when qtd_compra2 = 0 then 0 else compra/qtd_compra2 end as preco_medio_compra,
		   qtd_venda2,
  		   venda,
  		   case when qtd_venda2 = 0 then 0 else venda/qtd_venda2 end as preco_medio_venda,
  		   case when qtd_compra2 > 0 and qtd_venda2 > 0 and qtd_venda2 < qtd_compra2 then venda-compra/qtd_compra2*qtd_venda2
			 	when qtd_compra2 > 0 and qtd_venda2 > 0 and qtd_venda2 > qtd_compra2 then venda/qtd_venda2*qtd_compra2-compra end as resultado
  		   --case when qtd_compra2 = 0 then 0 else compra/qtd_compra2*
  	from base_swingtrade),
    
base_mensal as (
	select  
        extract(year from date)||FORMAT("%02d",extract(month from date)) as anomes,
  		  titulo,
  			sum(case when compra*1 > 0 then qtd else 0 end) as qtd_bought,
  			sum(case when venda*1 > 0 then qtd else 0 end) as qtd_sold,
  		  sum(qtd*ifnull(compra,0)) as bought,
  		  sum(qtd*ifnull(venda,0)) as sold,
  			sum(ifnull(inter_taxas,0)) as taxas
  	from stocks.notas_corretagem
	--where date <= '2019-12-31'
  	group by 1,2),

consolidacao_carteira as (
  	select 
		titulo,
		sum(qtd_compra) as qtd_compra,
		sum(qtd_venda) as qtd_venda,
		sum(compra) as compra,
		sum(venda) as venda
	from base_trades
	group by 1
),

consolidado_final as (
	select anomes,
			titulo,
			'intramonth' as tipo,
			resultado
	from (select * from base_swingtrade_apurada where resultado*1 > 0)
	union all 
	select anomes,
			titulo,
			'overmonth' as tipo,
			venda - compra as resultado
	from base_overmonth_apurada where cast(anomes as int64) > 0
	union ALL
	select 
      extract(year from date)||FORMAT("%02d",extract(month from date)) as anomes,
			titulo,
			max('daytrade') as tipo,
			sum(resultado) as resultado
	from base_trades
	where resultado <> 0
	group by 1,2)


select * from base_swingtrade_apurada