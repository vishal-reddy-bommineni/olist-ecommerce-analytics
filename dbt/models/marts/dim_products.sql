select product_id, category, is_missing_category, photos, description_length, weight_g
from {{ ref('stg_products') }}
