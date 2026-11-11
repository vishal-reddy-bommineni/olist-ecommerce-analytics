-- Monthly business KPIs over complete months only.
with o as (
    select * from {{ ref('fct_orders') }}
    where order_month >= '{{ var("analysis_start") }}' and order_month < '{{ var("analysis_end") }}'
)
select
    order_month,
    count(*) filter (where is_valid_order)                                   as orders,
    count(distinct customer_unique_id) filter (where is_valid_order)        as active_customers,
    count(*) filter (where is_valid_order and customer_order_number = 1)    as new_customer_orders,
    round(sum(order_value) filter (where is_valid_order), 2)                as gmv,
    round(sum(items_value) filter (where is_valid_order), 2)                as product_revenue,
    round(avg(order_value) filter (where is_valid_order), 2)                as avg_order_value,
    round(avg(case when is_late then 1.0 else 0.0 end) filter (where is_delivered), 4) as late_rate,
    round(avg(delivery_days) filter (where is_delivered), 2)                as avg_delivery_days,
    round(avg(review_score), 3)                                             as avg_review_score,
    round(count(*) filter (where order_status = 'canceled') * 1.0 / count(*), 4) as cancel_rate
from o
group by order_month
order by order_month
