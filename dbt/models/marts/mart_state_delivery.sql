-- Delivery performance and satisfaction by customer state (delivered orders).
select
    customer_state                                               as state,
    count(*)                                                     as delivered_orders,
    round(avg(delivery_days), 2)                                 as avg_delivery_days,
    round(median(delivery_days), 2)                              as median_delivery_days,
    round(avg(promised_days), 2)                                 as avg_promised_days,
    round(avg(case when is_late then 1.0 else 0.0 end), 4)       as late_rate,
    round(avg(freight_value / nullif(items_value, 0)), 4)        as avg_freight_to_price,
    round(avg(review_score), 3)                                  as avg_review_score
from {{ ref('fct_orders') }}
where is_delivered
group by customer_state
order by delivered_orders desc
