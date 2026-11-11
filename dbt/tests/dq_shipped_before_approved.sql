-- Handed to the carrier before the payment was approved.
{{ config(severity='warn', tags=['data_quality']) }}
select order_id from {{ ref('stg_orders') }}
where shipped_at < approved_at
