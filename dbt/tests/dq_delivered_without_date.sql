-- Status 'delivered' but no delivery date. Excluded from delivery analysis.
{{ config(severity='warn', tags=['data_quality']) }}
select order_id from {{ ref('stg_orders') }}
where order_status = 'delivered' and delivered_at is null
