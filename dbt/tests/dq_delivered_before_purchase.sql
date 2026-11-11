-- Impossible timelines: delivered or approved before the purchase.
{{ config(severity='warn', tags=['data_quality']) }}
select order_id from {{ ref('stg_orders') }}
where delivered_at < purchased_at or approved_at < purchased_at
