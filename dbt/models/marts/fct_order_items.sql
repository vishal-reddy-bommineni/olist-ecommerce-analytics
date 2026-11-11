-- One row per item sold (grain: order_id + order_item_id).
select
    i.order_id || '-' || i.order_item_id     as order_item_key,
    i.order_id,
    i.order_item_id,
    i.product_id,
    i.seller_id,
    o.customer_unique_id,
    o.customer_state,
    s.state                                  as seller_state,
    pr.category,
    o.order_status,
    o.is_valid_order,
    o.order_date,
    o.order_month,
    i.price,
    i.freight_value,
    o.is_late,
    o.review_score
from {{ ref('stg_order_items') }} i
join {{ ref('fct_orders') }} o using (order_id)
left join {{ ref('stg_products') }} pr using (product_id)
left join {{ ref('stg_sellers') }} s using (seller_id)
