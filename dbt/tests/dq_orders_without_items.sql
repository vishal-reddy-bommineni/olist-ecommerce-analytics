-- Orders that have no line items (mostly canceled/unavailable). Excluded from revenue.
{{ config(severity='warn', tags=['data_quality']) }}
select o.order_id, o.order_status
from {{ ref('stg_orders') }} o
left join {{ ref('stg_order_items') }} i using (order_id)
where i.order_id is null
