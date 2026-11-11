-- Payments rolled up to one row per order.
select
    order_id,
    sum(payment_value)                                   as payment_total,
    count(*)                                             as payment_rows,
    max(payment_installments)                            as max_installments,
    -- the payment type that covered most of the order value
    arg_max(payment_type, payment_value)                 as main_payment_type,
    bool_or(payment_type = 'voucher')                    as used_voucher
from {{ ref('stg_payments') }}
group by order_id
