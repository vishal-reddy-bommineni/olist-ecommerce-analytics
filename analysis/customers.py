"""Retention and repeat purchase."""
from analysis.common import df


def repeat_summary():
    return df("""
        select count(*) as customers,
               sum(is_repeat_customer::int) as repeat_customers,
               avg(is_repeat_customer::int) as repeat_rate,
               sum(lifetime_value) filter (where is_repeat_customer) / sum(lifetime_value) as repeat_revenue_share,
               avg(orders) filter (where is_repeat_customer) as orders_per_repeat_customer
        from marts.dim_customers""").iloc[0].to_dict()


def days_to_second_order():
    """Time from first purchase to the first purchase on a LATER day."""
    return df("""
        with o as (select customer_unique_id, purchased_at::date as d from intermediate.int_customer_orders),
        firsts as (select customer_unique_id, min(d) as d1 from o group by 1),
        seconds as (select f.customer_unique_id, f.d1, min(o.d) as d2
                    from firsts f join o on o.customer_unique_id = f.customer_unique_id and o.d > f.d1
                    group by 1, 2)
        select count(*) as returning_customers,
               median(date_diff('day', d1, d2)) as median_days,
               avg((date_diff('day', d1, d2) <= 90)::int) as share_within_90d
        from seconds""").iloc[0].to_dict()


def same_day_split_orders():
    """Customers whose only 'repeat' is a second order placed the same day."""
    return df("""
        select count(*) filter (where orders > 1 and purchase_days = 1) as same_day_only,
               count(*) filter (where orders > 1) as multi_order_customers
        from marts.dim_customers""").iloc[0].to_dict()


def retention_curve():
    return df("""
        select months_since_first,
               sum(active_customers) * 1.0 / sum(cohort_size) as retention,
               count(*) as cohorts
        from marts.mart_cohort_retention
        where months_since_first between 1 and 12
        group by 1 order by 1""")


def retention_matrix():
    return df("""
        select strftime(cohort_month, '%Y-%m') as cohort, cohort_size, months_since_first, retention_rate
        from marts.mart_cohort_retention
        where months_since_first <= 12""")


def first_review_vs_return():
    """Do customers whose first order went badly come back less?"""
    return df("""
        with first as (
            select f.customer_unique_id, f.review_score, f.is_late
            from marts.fct_orders f
            where f.customer_order_number = 1 and f.is_delivered
              and f.order_month < '2018-03-01'          -- leaves at least 6 months to return
        )
        select case when review_score <= 2 then 'first review 1-2'
                    when review_score = 3 then 'first review 3'
                    when review_score >= 4 then 'first review 4-5' end as first_experience,
               count(*) as customers,
               avg(d.is_repeat_customer::int) as repeat_rate
        from first join marts.dim_customers d using (customer_unique_id)
        where review_score is not null
        group by 1 order by 1""")
