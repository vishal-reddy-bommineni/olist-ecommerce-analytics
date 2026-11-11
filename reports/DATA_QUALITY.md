# Data quality (auto-generated from dbt test results, do not edit)

dbt build: 21 models, 55 tests: 46 pass, 9 warn, 0 fail.

## Known source issues (warning-level checks)

These are real issues in the Olist data. The checks warn rather than fail, and each is handled in the models.

| Check | Rows found | Handling |
|---|---|---|
| Handed to carrier before payment approval (`dq_shipped_before_approved`) | 1,359 | Kept; not used in any metric |
| Orders with no line items (`dq_orders_without_items`) | 775 | Mostly canceled/unavailable; contribute R$0 to revenue |
| Products with no category (`dq_missing_category`) | 610 | Labelled 'unknown' |
| Orders with 2+ reviews (`dq_duplicate_reviews`) | 547 | Latest answered review kept (`stg_reviews`) |
| Payments differ from items + freight by > R$1 (`dq_payment_mismatch`) | 249 | Revenue uses items + freight; payments kept separately |
| 'delivered' orders with no delivery date (`dq_delivered_without_date`) | 8 | Excluded from delivery analysis (`is_delivered` = false) |
| Canceled orders that have a delivery date (`dq_canceled_with_delivery_date`) | 6 | Status is trusted; treated as invalid orders |
| Categories missing from the translation file (`dq_untranslated_category`) | 2 | Portuguese name kept |
| Orders with no payment record (`dq_orders_without_payment`) | 1 | Kept; payment fields are NULL |
| Delivered or approved before purchase (`dq_delivered_before_purchase`) | 0 | None found |

## Integrity checks (must pass)

Primary keys unique and not null, foreign keys resolve, accepted values, value ranges, and reconciliation between layers (no item lost between staging and marts; monthly GMV equals the order-level total).

| Test | Status |
|---|---|
| `accepted_values_stg_orders_order_status__delivered__shipped__canceled__unavailable__invoiced__processing__created__approved` | pass |
| `accepted_values_stg_payments_payment_type__credit_card__boleto__voucher__debit_card__not_defined` | pass |
| `accepted_values_stg_reviews_review_score__False__1__2__3__4__5` | pass |
| `assert_gmv_reconciles` | pass |
| `assert_items_reconcile` | pass |
| `between_zero_and_one_mart_cohort_retention_retention_rate` | pass |
| `not_null_dim_customers_customer_unique_id` | pass |
| `not_null_dim_date_date` | pass |
| `not_null_dim_products_product_id` | pass |
| `not_null_dim_sellers_seller_id` | pass |
| `not_null_fct_order_items_order_item_key` | pass |
| `not_null_fct_orders_customer_unique_id` | pass |
| `not_null_fct_orders_order_id` | pass |
| `not_null_mart_monthly_kpis_order_month` | pass |
| `not_null_seller_scorecard_seller_id` | pass |
| `not_null_stg_customers_customer_id` | pass |
| `not_null_stg_customers_customer_unique_id` | pass |
| `not_null_stg_order_items_order_id` | pass |
| `not_null_stg_order_items_price` | pass |
| `not_null_stg_orders_customer_id` | pass |
| `not_null_stg_orders_order_id` | pass |
| `not_null_stg_products_product_id` | pass |
| `not_null_stg_reviews_order_id` | pass |
| `not_null_stg_sellers_seller_id` | pass |
| `positive_value_stg_order_items_price` | pass |
| `relationships_stg_order_items_order_id__order_id__ref_stg_orders_` | pass |
| `relationships_stg_order_items_product_id__product_id__ref_stg_products_` | pass |
| `relationships_stg_order_items_seller_id__seller_id__ref_stg_sellers_` | pass |
| `relationships_stg_orders_customer_id__customer_id__ref_stg_customers_` | pass |
| `relationships_stg_payments_order_id__order_id__ref_stg_orders_` | pass |
| `unique_combination_of_columns_mart_cohort_retention_cohort_month__months_since_first` | pass |
| `unique_combination_of_columns_stg_order_items_order_id__order_item_id` | pass |
| `unique_dim_customers_customer_unique_id` | pass |
| `unique_dim_date_date` | pass |
| `unique_dim_products_product_id` | pass |
| `unique_dim_sellers_seller_id` | pass |
| `unique_fct_order_items_order_item_key` | pass |
| `unique_fct_orders_order_id` | pass |
| `unique_mart_monthly_kpis_order_month` | pass |
| `unique_seller_scorecard_seller_id` | pass |
| `unique_stg_customers_customer_id` | pass |
| `unique_stg_orders_order_id` | pass |
| `unique_stg_products_product_id` | pass |
| `unique_stg_reviews_order_id` | pass |
| `unique_stg_sellers_seller_id` | pass |
