-- Products with no category in the source (labelled 'unknown').
{{ config(severity='warn', tags=['data_quality']) }}
select product_id from {{ ref('stg_products') }} where is_missing_category
