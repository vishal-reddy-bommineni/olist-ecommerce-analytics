-- One row per order. Statuses and timestamps cleaned; delivery metrics derived.
select
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp                                   as purchased_at,
    order_approved_at                                          as approved_at,
    order_delivered_carrier_date                               as shipped_at,
    order_delivered_customer_date                              as delivered_at,
    order_estimated_delivery_date                              as estimated_delivery_at,
    date_trunc('month', order_purchase_timestamp)::date        as order_month,
    -- canceled / unavailable orders never generated sales
    order_status not in ('canceled', 'unavailable')            as is_valid_order,
    -- usable for delivery analysis: delivered and actually has a delivery date
    (order_status = 'delivered' and order_delivered_customer_date is not null) as is_delivered,
    round(epoch(order_delivered_customer_date - order_purchase_timestamp) / 86400.0, 2)  as delivery_days,
    round(epoch(order_estimated_delivery_date - order_purchase_timestamp) / 86400.0, 2)  as promised_days,
    -- the estimate is a date (midnight), so lateness is judged by calendar day
    date_diff('day', order_estimated_delivery_date::date, order_delivered_customer_date::date) as days_late
from {{ source('raw', 'orders') }}
