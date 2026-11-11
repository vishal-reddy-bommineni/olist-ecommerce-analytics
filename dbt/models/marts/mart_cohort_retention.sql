-- Share of each monthly acquisition cohort that ordered again N months later.
with orders as (
    select customer_unique_id, order_month from {{ ref('int_customer_orders') }}
),
cohorts as (
    select customer_unique_id, cohort_month from {{ ref('dim_customers') }}
    where cohort_month >= '{{ var("analysis_start") }}' and cohort_month < '{{ var("analysis_end") }}'
),
activity as (
    select distinct c.cohort_month, c.customer_unique_id,
           date_diff('month', c.cohort_month, o.order_month) as months_since_first
    from cohorts c join orders o using (customer_unique_id)
),
sizes as (
    select cohort_month, count(*) as cohort_size from cohorts group by cohort_month
)
select
    a.cohort_month,
    s.cohort_size,
    a.months_since_first,
    count(*)                                         as active_customers,
    round(count(*) * 1.0 / s.cohort_size, 5)         as retention_rate
from activity a join sizes s using (cohort_month)
where a.cohort_month + to_months(a.months_since_first) < '{{ var("analysis_end") }}'::date
group by a.cohort_month, s.cohort_size, a.months_since_first
order by a.cohort_month, a.months_since_first
