# Data

**Brazilian E-Commerce Public Dataset by Olist**: about 100,000 real, anonymised orders placed
between 2016 and 2018 on the Olist marketplace in Brazil, with items, payments, reviews, products,
sellers and customers.

- Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- License: CC BY-NC-SA 4.0 (attribution, non-commercial, share-alike). The derived tables in
  `data/marts/` are shared under the same license.
- Company names in reviews were replaced with Game of Thrones house names by Olist.

## Getting the files
Download the zip from Kaggle (free account) and extract the CSVs into `data/raw/`:

| File | Used as |
|---|---|
| olist_orders_dataset.csv | raw.orders |
| olist_customers_dataset.csv | raw.customers |
| olist_order_items_dataset.csv | raw.order_items |
| olist_order_payments_dataset.csv | raw.order_payments |
| olist_order_reviews_dataset.csv | raw.order_reviews |
| olist_products_dataset.csv | raw.products |
| olist_sellers_dataset.csv | raw.sellers |
| product_category_name_translation.csv | raw.category_translation |

`olist_geolocation_dataset.csv` is not used. The raw CSVs are not committed (size and license);
the dashboard runs from the committed Parquet marts in `data/marts/`.
