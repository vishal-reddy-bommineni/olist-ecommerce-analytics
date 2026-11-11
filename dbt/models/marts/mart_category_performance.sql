-- Revenue, growth and satisfaction by product category (valid orders, complete months).
with i as (
    select * from {{ ref('fct_order_items') }}
    where is_valid_order
      and order_month >= '{{ var("analysis_start") }}' and order_month < '{{ var("analysis_end") }}'
)
select
    category,
    count(distinct order_id)                                           as orders,
    count(*)                                                           as items,
    round(sum(price), 2)                                               as revenue,
    round(sum(price) * 1.0 / sum(sum(price)) over (), 5)               as revenue_share,
    round(avg(price), 2)                                               as avg_item_price,
    round(sum(freight_value) / nullif(sum(price), 0), 4)               as freight_to_price,
    round(avg(review_score), 3)                                        as avg_review_score,
    round(avg(case when is_late then 1.0 else 0.0 end) filter (where is_late is not null), 4) as late_rate,
    -- H1 2018 vs H1 2017 revenue growth
    round(sum(price) filter (where order_month between '2018-01-01' and '2018-06-01')
        / nullif(sum(price) filter (where order_month between '2017-01-01' and '2017-06-01'), 0) - 1, 4) as growth_h1_2018_vs_2017
from i
group by category
order by revenue desc
