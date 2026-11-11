-- Orders with more than one review in the source (deduplicated in stg_reviews).
{{ config(severity='warn', tags=['data_quality']) }}
select order_id, count(*) as reviews
from {{ source('raw', 'order_reviews') }}
group by order_id having count(*) > 1
