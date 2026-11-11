-- One row per real customer (customer_unique_id), with acquisition cohort and value.
-- Repeat customer = bought again on a later day.
with orders as (
    select * from {{ ref('fct_orders') }} where is_valid_order
),
latest_location as (
    select customer_unique_id, customer_state,
           row_number() over (partition by customer_unique_id order by purchased_at desc) as rn
    from {{ ref('fct_orders') }}
)
select
    o.customer_unique_id,
    l.customer_state                             as state,
    min(o.purchased_at)                          as first_order_at,
    date_trunc('month', min(o.purchased_at))::date as cohort_month,
    max(o.purchased_at)                          as last_order_at,
    count(*)                                     as orders,
    count(distinct o.order_date)                 as purchase_days,
    sum(o.order_value)                           as lifetime_value,
    avg(o.review_score)                          as avg_review_score,
    -- a second order on the SAME day is usually a split checkout, not a return visit
    count(distinct o.order_date) > 1             as is_repeat_customer
from orders o
join latest_location l on l.customer_unique_id = o.customer_unique_id and l.rn = 1
group by o.customer_unique_id, l.customer_state
