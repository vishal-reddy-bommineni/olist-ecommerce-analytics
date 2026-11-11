-- Hard check: no item is lost or duplicated between staging and the item fact table.
select (select count(*) from {{ ref('stg_order_items') }}) as stg,
       (select count(*) from {{ ref('fct_order_items') }}) as fct
where (select count(*) from {{ ref('stg_order_items') }}) <> (select count(*) from {{ ref('fct_order_items') }})
