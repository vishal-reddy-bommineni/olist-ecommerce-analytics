# Business questions in SQL (auto-generated, do not edit)

Queries: `sql/business_questions.sql`. Run against the dbt marts.

## How did GMV change month over month, and what was the 3-month moving average?

`mom_growth`

```sql
select
    strftime(order_month, '%Y-%m')                                           as month,
    gmv,
    round(gmv / lag(gmv) over (order by order_month) - 1, 4)                as mom_growth,
    round(avg(gmv) over (order by order_month rows between 2 preceding and current row), 2) as gmv_3m_avg
from marts.mart_monthly_kpis
order by order_month
```

| month | gmv | mom_growth | gmv_3m_avg |
|---|---|---|---|
| 2017-01 | 136,943.46 | - | 136,943.46 |
| 2017-02 | 283,561.69 | 1.07 | 210,252.58 |
| 2017-03 | 425,617.96 | 0.501 | 282,041.04 |
| 2017-04 | 405,848.61 | -0.0464 | 371,676.09 |
| 2017-05 | 582,710.83 | 0.4358 | 471,392.47 |
| 2017-06 | 499,652.24 | -0.1425 | 496,070.56 |
| 2017-07 | 578,753.73 | 0.1583 | 553,705.60 |
| 2017-08 | 661,903.52 | 0.1437 | 580,103.16 |
| 2017-09 | 717,102.72 | 0.0834 | 652,586.66 |
| 2017-10 | 764,756.03 | 0.0665 | 714,587.42 |
| 2017-11 | 1,172,191.68 | 0.5328 | 884,683.48 |
| 2017-12 | 861,526.77 | -0.265 | 932,824.83 |
| 2018-01 | 1,101,920.01 | 0.279 | 1,045,212.82 |
| 2018-02 | 979,486.16 | -0.1111 | 980,977.65 |
| 2018-03 | 1,152,656.99 | 0.1768 | 1,078,021.05 |
| 2018-04 | 1,156,248.89 | 0.0031 | 1,096,130.68 |
| 2018-05 | 1,145,686.46 | -0.0091 | 1,151,530.78 |
| 2018-06 | 1,020,381.90 | -0.1094 | 1,107,439.08 |
| 2018-07 | 1,039,783.58 | 0.019 | 1,068,617.31 |
| 2018-08 | 996,973.51 | -0.0412 | 1,019,046.33 |

## Which were the 5 biggest sales days, and how did they compare with the average day that month?

`black_friday`

```sql
with daily as (
    select order_date, count(*) as orders, sum(order_value) as gmv
    from marts.fct_orders where is_valid_order group by order_date
)
select strftime(order_date, '%Y-%m-%d') as order_date, orders, round(gmv, 2) as gmv,
       round(orders / avg(orders) over (partition by date_trunc('month', order_date)), 2) as x_month_avg
from daily
qualify rank() over (order by orders desc) <= 5
order by orders desc
```

| order_date | orders | gmv | x_month_avg |
|---|---|---|---|
| 2017-11-24 | 1166 | 178,377.63 | 4.71 |
| 2017-11-25 | 499 | 71,858.16 | 2.02 |
| 2017-11-27 | 400 | 56,644.85 | 1.62 |
| 2017-11-26 | 387 | 53,245.63 | 1.56 |
| 2017-11-28 | 376 | 56,248.47 | 1.52 |

## How do customers pay, and do installment plans go with bigger baskets?

`payment_mix`

```sql
select main_payment_type,
       count(*)                                   as orders,
       round(count(*) * 1.0 / sum(count(*)) over (), 4) as share,
       round(avg(order_value), 2)                 as avg_order_value,
       round(avg(max_installments), 2)            as avg_installments
from marts.fct_orders
where is_valid_order and main_payment_type is not null
group by 1 order by orders desc
```

| main_payment_type | orders | share | avg_order_value | avg_installments |
|---|---|---|---|---|
| credit_card | 74116 | 0.7547 | 166.60 | 3.55 |
| boleto | 19539 | 0.199 | 144.66 | 1 |
| voucher | 3037 | 0.0309 | 114.93 | 1.15 |
| debit_card | 1514 | 0.0154 | 140.30 | 1 |

## Average order value by number of installments (credit card only).

`installments_vs_value`

```sql
select case when max_installments <= 1 then '1' when max_installments <= 3 then '2-3'
            when max_installments <= 6 then '4-6' else '7+' end as installments,
       count(*) as orders, round(avg(order_value), 2) as avg_order_value
from marts.fct_orders
where is_valid_order and main_payment_type = 'credit_card'
group by 1 order by min(max_installments)
```

| installments | orders | avg_order_value |
|---|---|---|
| 1 | 23725 | 100.78 |
| 2-3 | 22408 | 135.24 |
| 4-6 | 15977 | 182.06 |
| 7+ | 12006 | 334.58 |

## What is the best-selling category (by revenue) in each of the 10 largest states?

`top_category_per_state`

```sql
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
order by state_revenue desc
```

| customer_state | category | revenue | share_of_state |
|---|---|---|---|
| SP | bed_bath_table | 477,794.20 | 0.0925 |
| RJ | watches_gifts | 183,931.50 | 0.1015 |
| MG | health_beauty | 157,433.32 | 0.1001 |
| RS | bed_bath_table | 60,270.74 | 0.0812 |
| PR | watches_gifts | 59,859.04 | 0.0884 |
| SC | sports_leisure | 43,466.90 | 0.0838 |
| BA | health_beauty | 51,217.91 | 0.101 |
| DF | watches_gifts | 32,730.37 | 0.1088 |
| GO | watches_gifts | 32,358.72 | 0.1124 |
| ES | watches_gifts | 29,461 | 0.1077 |

## Are orders shipped from another state later and rated worse than same-state orders?

`cross_state_shipping`

```sql
select case when seller_state = customer_state then 'same state' else 'other state' end as route,
       count(distinct order_id) as orders,
       round(avg(is_late::int), 4) as late_rate,
       round(avg(review_score), 3) as avg_review,
       round(avg(freight_value / nullif(price, 0)), 4) as freight_to_price
from marts.fct_order_items
where is_valid_order and is_late is not null
group by 1 order by 1
```

| route | orders | late_rate | avg_review | freight_to_price |
|---|---|---|---|---|
| other state | 61895 | 0.0781 | 4.02 | 0.3602 |
| same state | 34822 | 0.0445 | 4.20 | 0.2514 |

## How many sellers make up 50%, 80% and 95% of revenue?

`seller_pareto`

```sql
with r as (
    select revenue, sum(revenue) over (order by revenue desc rows unbounded preceding) / sum(revenue) over () as cum_share,
           row_number() over (order by revenue desc) as n
    from marts.seller_scorecard
)
select target, min(n) as sellers_needed, round(min(n) * 1.0 / (select count(*) from r), 4) as share_of_sellers
from r, (values (0.5), (0.8), (0.95)) t(target)
where cum_share >= target
group by target order by target
```

| target | sellers_needed | share_of_sellers |
|---|---|---|
| 0.5 | 129 | 0.0423 |
| 0.8 | 540 | 0.1769 |
| 0.95 | 1293 | 0.4235 |

## When customers come back, do they buy from the same category?

`second_order_category`

```sql
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
from cats where len(later_cats) > 0
```

| returning_customers | bought_same_category_again | share |
|---|---|---|
| 2064 | 827 | 0.4007 |

## Are unhappy customers more likely to write a comment?

`review_comment_rate`

```sql
select review_score, count(*) as reviews, round(avg(review_has_comment::int), 4) as comment_rate
from marts.fct_orders where review_score is not null
group by 1 order by 1
```

| review_score | reviews | comment_rate |
|---|---|---|
| 1 | 11363 | 0.7662 |
| 2 | 3131 | 0.6813 |
| 3 | 8133 | 0.435 |
| 4 | 19038 | 0.3123 |
| 5 | 57008 | 0.3586 |

## On which weekdays do people order?

`weekday_pattern`

```sql
select dayname(purchased_at) as weekday, isodow(purchased_at) as dow,
       count(*) as orders, round(count(*) * 1.0 / sum(count(*)) over (), 4) as share
from marts.fct_orders where is_valid_order
group by 1, 2 order by dow
```

| weekday | dow | orders | share |
|---|---|---|---|
| Monday | 1 | 15979 | 0.1627 |
| Tuesday | 2 | 15760 | 0.1605 |
| Wednesday | 3 | 15353 | 0.1563 |
| Thursday | 4 | 14571 | 0.1484 |
| Friday | 5 | 13949 | 0.142 |
| Saturday | 6 | 10764 | 0.1096 |
| Sunday | 7 | 11831 | 0.1205 |
