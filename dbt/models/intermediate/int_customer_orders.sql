-- Valid orders per real customer (customer_unique_id), numbered in purchase order.
select
    c.customer_unique_id,
    o.order_id,
    o.purchased_at,
    o.order_month,
    row_number() over (partition by c.customer_unique_id order by o.purchased_at, o.order_id) as order_number
from {{ ref('stg_orders') }} o
join {{ ref('stg_customers') }} c using (customer_id)
where o.is_valid_order
