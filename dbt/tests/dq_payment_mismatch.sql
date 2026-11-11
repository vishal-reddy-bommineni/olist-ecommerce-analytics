-- Orders where payments differ from items + freight by more than R$1 (vouchers, interest on installments).
{{ config(severity='warn', tags=['data_quality']) }}
select i.order_id, i.order_value, p.payment_total, p.payment_total - i.order_value as diff
from {{ ref('int_order_items_agg') }} i
join {{ ref('int_order_payments') }} p using (order_id)
where abs(p.payment_total - i.order_value) > 1
