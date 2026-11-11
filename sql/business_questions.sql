-- Business questions answered directly in SQL against the dbt marts.
-- Each query starts with a "-- name:" line and a question; scripts/run_business_questions.py runs them all
-- and writes reports/business_questions.md.

-- name: mom_growth
-- Q: How did GMV change month over month, and what was the 3-month moving average?
select
    strftime(order_month, '%Y-%m')                                           as month,
    gmv,
    round(gmv / lag(gmv) over (order by order_month) - 1, 4)                as mom_growth,
    round(avg(gmv) over (order by order_month rows between 2 preceding and current row), 2) as gmv_3m_avg
from marts.mart_monthly_kpis
order by order_month;

-- name: black_friday
-- Q: Which were the 5 biggest sales days, and how did they compare with the average day that month?
with daily as (
    select order_date, count(*) as orders, sum(order_value) as gmv
    from marts.fct_orders where is_valid_order group by order_date
)
select strftime(order_date, '%Y-%m-%d') as order_date, orders, round(gmv, 2) as gmv,
       round(orders / avg(orders) over (partition by date_trunc('month', order_date)), 2) as x_month_avg
from daily
qualify rank() over (order by orders desc) <= 5
order by orders desc;

-- name: payment_mix
-- Q: How do customers pay, and do installment plans go with bigger baskets?
select main_payment_type,
       count(*)                                   as orders,
       round(count(*) * 1.0 / sum(count(*)) over (), 4) as share,
       round(avg(order_value), 2)                 as avg_order_value,
       round(avg(max_installments), 2)            as avg_installments
from marts.fct_orders
where is_valid_order and main_payment_type is not null
group by 1 order by orders desc;

-- name: installments_vs_value
-- Q: Average order value by number of installments (credit card only).
select case when max_installments <= 1 then '1' when max_installments <= 3 then '2-3'
            when max_installments <= 6 then '4-6' else '7+' end as installments,
       count(*) as orders, round(avg(order_value), 2) as avg_order_value
from marts.fct_orders
where is_valid_order and main_payment_type = 'credit_card'
group by 1 order by min(max_installments);

-- name: top_category_per_state
-- Q: What is the best-selling category (by revenue) in each of the 10 largest states?
with s as (
    select customer_state, category, sum(price) as revenue
    from marts.fct_order_items where is_valid_order group by 1, 2
),
ranked as (
    select *, row_number() over (partition by customer_state order by revenue desc) as rn,
           sum(revenue) over (partition by customer_state) as state_revenue
    from s
)
select customer_state, category, round(revenue, 2) as revenue, round(revenue / state_revenue, 4) as share_of_state
from ranked
where rn = 1 and customer_state in (
    select customer_state from marts.fct_orders group by 1 order by count(*) desc limit 10)
order by state_revenue desc;

-- name: cross_state_shipping
-- Q: Are orders shipped from another state later and rated worse than same-state orders?
select case when seller_state = customer_state then 'same state' else 'other state' end as route,
       count(distinct order_id) as orders,
       round(avg(is_late::int), 4) as late_rate,
       round(avg(review_score), 3) as avg_review,
       round(avg(freight_value / nullif(price, 0)), 4) as freight_to_price
from marts.fct_order_items
where is_valid_order and is_late is not null
group by 1 order by 1;

-- name: seller_pareto
-- Q: How many sellers make up 50%, 80% and 95% of revenue?
with r as (
    select revenue, sum(revenue) over (order by revenue desc rows unbounded preceding) / sum(revenue) over () as cum_share,
           row_number() over (order by revenue desc) as n
    from marts.seller_scorecard
)
select target, min(n) as sellers_needed, round(min(n) * 1.0 / (select count(*) from r), 4) as share_of_sellers
from r, (values (0.5), (0.8), (0.95)) t(target)
where cum_share >= target
group by target order by target;

-- name: second_order_category
-- Q: When customers come back, do they buy from the same category?
with firsts as (
    select o.customer_unique_id, o.purchased_at::date as d, i.category
    from marts.fct_orders o join marts.fct_order_items i using (order_id)
    where o.is_valid_order
),
first_day as (
    select customer_unique_id, min(d) as d1 from firsts group by 1
),
cats as (
    select f.customer_unique_id,
           list_distinct(list(f.category) filter (where f.d = fd.d1)) as first_cats,
           list_distinct(list(f.category) filter (where f.d > fd.d1)) as later_cats
    from firsts f join first_day fd using (customer_unique_id)
    group by 1
)
select count(*) as returning_customers,
       sum((len(list_intersect(first_cats, later_cats)) > 0)::int) as bought_same_category_again,
       round(avg((len(list_intersect(first_cats, later_cats)) > 0)::int), 4) as share
from cats where len(later_cats) > 0;

-- name: review_comment_rate
-- Q: Are unhappy customers more likely to write a comment?
select review_score, count(*) as reviews, round(avg(review_has_comment::int), 4) as comment_rate
from marts.fct_orders where review_score is not null
group by 1 order by 1;

-- name: weekday_pattern
-- Q: On which weekdays do people order?
select dayname(purchased_at) as weekday, isodow(purchased_at) as dow,
       count(*) as orders, round(count(*) * 1.0 / sum(count(*)) over (), 4) as share
from marts.fct_orders where is_valid_order
group by 1, 2 order by dow;
