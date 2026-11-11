-- Hard check: monthly GMV in the KPI mart must equal the order-level fact table.
select m.order_month, m.gmv, f.gmv as fact_gmv
from {{ ref('mart_monthly_kpis') }} m
join (
    select order_month, round(sum(order_value), 2) as gmv
    from {{ ref('fct_orders') }} where is_valid_order group by order_month
) f using (order_month)
where abs(m.gmv - f.gmv) > 0.01
