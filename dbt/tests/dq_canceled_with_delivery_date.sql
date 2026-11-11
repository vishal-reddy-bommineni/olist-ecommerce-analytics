-- Canceled orders that still have a customer delivery date (status and timestamps disagree).
{{ config(severity='warn', tags=['data_quality']) }}
select order_id from {{ ref('stg_orders') }}
where order_status = 'canceled' and delivered_at is not null
