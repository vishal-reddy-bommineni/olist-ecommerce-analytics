-- English category names. 610 products have no category ('unknown'); two categories are
-- missing from the translation file, so their Portuguese name is kept.
select
    p.product_id,
    coalesce(t.product_category_name_english, p.product_category_name, 'unknown') as category,
    p.product_category_name is null                     as is_missing_category,
    p.product_photos_qty                                as photos,
    p.product_description_lenght                        as description_length,   -- source typo: "lenght"
    p.product_weight_g                                  as weight_g
from {{ source('raw', 'products') }} p
left join {{ source('raw', 'category_translation') }} t
    on p.product_category_name = t.product_category_name
