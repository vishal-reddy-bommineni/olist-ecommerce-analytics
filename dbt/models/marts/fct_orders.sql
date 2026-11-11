-- One row per order: the main fact table.
select
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.state                                  as customer_state,
    o.order_status,
    o.is_valid_order,
    o.is_delivered,
    o.purchased_at,
    o.purchased_at::date                     as order_date,
    o.order_month,
    o.approved_at,
    o.shipped_at,
    o.delivered_at,
    o.estimated_delivery_at,
    o.delivery_days,
    o.promised_days,
    o.days_late,
    case when o.is_delivered then o.days_late > 0 end            as is_late,
    coalesce(i.items, 0)                     as items,
    i.distinct_sellers,
    coalesce(i.items_value, 0)               as items_value,
    coalesce(i.freight_value, 0)             as freight_value,
    coalesce(i.order_value, 0)               as order_value,
    p.payment_total,
    p.main_payment_type,
    p.max_installments,
    r.review_score,
    r.has_comment                            as review_has_comment,
    co.order_number                          as customer_order_number
from {{ ref('stg_orders') }} o
join {{ ref('stg_customers') }} c using (customer_id)
left join {{ ref('int_order_items_agg') }} i using (order_id)
left join {{ ref('int_order_payments') }} p using (order_id)
left join {{ ref('stg_reviews') }} r using (order_id)
left join {{ ref('int_customer_orders') }} co using (order_id)
