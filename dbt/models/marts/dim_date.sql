-- Calendar covering the full order history (for Power BI time intelligence).
with bounds as (
    select min(order_date) as d0, max(order_date) as d1 from {{ ref('fct_orders') }}
)
select
    d::date                                   as date,
    year(d)                                   as year,
    quarter(d)                                as quarter,
    month(d)                                  as month,
    strftime(d, '%b')                         as month_name,
    date_trunc('month', d)::date              as month_start,
    isodow(d)                                 as weekday_number,
    strftime(d, '%a')                         as weekday_name,
    isodow(d) in (6, 7)                       as is_weekend
from bounds, range(bounds.d0, bounds.d1 + interval 1 day, interval 1 day) t(d)
