-- Categories missing from the English translation file.
{{ config(severity='warn', tags=['data_quality']) }}
select distinct p.product_category_name
from {{ source('raw', 'products') }} p
left join {{ source('raw', 'category_translation') }} t using (product_category_name)
where p.product_category_name is not null and t.product_category_name is null
