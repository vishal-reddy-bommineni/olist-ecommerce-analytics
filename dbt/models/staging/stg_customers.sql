-- customer_id is a per-ORDER key in Olist; customer_unique_id identifies the person.
-- Using customer_id for retention would make every customer look like a first-time buyer.
select
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix   as zip_prefix,
    customer_city              as city,
    upper(customer_state)      as state
from {{ source('raw', 'customers') }}
