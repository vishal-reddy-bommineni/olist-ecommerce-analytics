-- Seller scorecard: volume, revenue, delivery and satisfaction, with a simple risk flag.
-- Sellers with fewer than var('min_seller_orders') orders are kept but not flagged.
with items as (
    select * from {{ ref('fct_order_items') }} where is_valid_order
),
per_seller_order as (
    -- one row per seller x order so late / review are not counted once per item
    select seller_id, order_id, any_value(is_late) as is_late, any_value(review_score) as review_score,
           sum(price) as revenue, sum(freight_value) as freight
    from items group by seller_id, order_id
),
agg as (
    select
        seller_id,
        count(*)                                                     as orders,
        round(sum(revenue), 2)                                       as revenue,
        round(sum(freight), 2)                                       as freight,
        round(avg(case when is_late then 1.0 else 0.0 end) filter (where is_late is not null), 4) as late_rate,
        round(avg(review_score), 3)                                  as avg_review_score,
        round(avg(case when review_score <= 2 then 1.0 else 0.0 end) filter (where review_score is not null), 4) as low_review_rate
    from per_seller_order group by seller_id
)
select
    a.seller_id,
    s.state,
    s.city,
    a.orders,
    a.revenue,
    round(a.revenue / sum(a.revenue) over (), 6)                     as revenue_share,
    row_number() over (order by a.revenue desc)                      as revenue_rank,
    a.late_rate,
    a.avg_review_score,
    a.low_review_rate,
    a.orders >= {{ var('min_seller_orders') }}                       as is_established,
    (a.orders >= {{ var('min_seller_orders') }}
        and (a.late_rate > 0.15 or a.low_review_rate > 0.25))        as is_at_risk
from agg a
left join {{ ref('stg_sellers') }} s using (seller_id)
