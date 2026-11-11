{{ config(severity='warn', tags=['data_quality']) }}
select o.order_id from {{ ref('stg_orders') }} o
left join {{ ref('int_order_payments') }} p using (order_id)
where p.order_id is null
