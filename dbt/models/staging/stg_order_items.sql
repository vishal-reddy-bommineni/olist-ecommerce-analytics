select
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_date        as shipping_limit_at,
    price::double              as price,
    freight_value::double      as freight_value
from {{ source('raw', 'order_items') }}
