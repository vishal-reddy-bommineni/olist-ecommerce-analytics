"""Step 1: load the Olist CSVs into DuckDB (schema `raw`) with explicit column types.

Usage:  python -m src.load_raw
Why explicit types: ZIP code prefixes like "01310" must stay text (type inference turns them
into numbers and drops the leading zero), and every timestamp should be a real TIMESTAMP.
Column names are set explicitly too, because the translation file starts with an invisible
byte-order mark (BOM) in its first header.
"""
import duckdb

from src.config import DB_PATH, RAW_DIR

TABLES = {
    "orders": ("olist_orders_dataset.csv", {
        "order_id": "VARCHAR", "customer_id": "VARCHAR", "order_status": "VARCHAR",
        "order_purchase_timestamp": "TIMESTAMP", "order_approved_at": "TIMESTAMP",
        "order_delivered_carrier_date": "TIMESTAMP", "order_delivered_customer_date": "TIMESTAMP",
        "order_estimated_delivery_date": "TIMESTAMP"}),
    "customers": ("olist_customers_dataset.csv", {
        "customer_id": "VARCHAR", "customer_unique_id": "VARCHAR",
        "customer_zip_code_prefix": "VARCHAR", "customer_city": "VARCHAR", "customer_state": "VARCHAR"}),
    "order_items": ("olist_order_items_dataset.csv", {
        "order_id": "VARCHAR", "order_item_id": "INTEGER", "product_id": "VARCHAR", "seller_id": "VARCHAR",
        "shipping_limit_date": "TIMESTAMP", "price": "DECIMAL(10,2)", "freight_value": "DECIMAL(10,2)"}),
    "order_payments": ("olist_order_payments_dataset.csv", {
        "order_id": "VARCHAR", "payment_sequential": "INTEGER", "payment_type": "VARCHAR",
        "payment_installments": "INTEGER", "payment_value": "DECIMAL(10,2)"}),
    "order_reviews": ("olist_order_reviews_dataset.csv", {
        "review_id": "VARCHAR", "order_id": "VARCHAR", "review_score": "INTEGER",
        "review_comment_title": "VARCHAR", "review_comment_message": "VARCHAR",
        "review_creation_date": "TIMESTAMP", "review_answer_timestamp": "TIMESTAMP"}),
    "products": ("olist_products_dataset.csv", {
        "product_id": "VARCHAR", "product_category_name": "VARCHAR", "product_name_lenght": "INTEGER",
        "product_description_lenght": "INTEGER", "product_photos_qty": "INTEGER", "product_weight_g": "INTEGER",
        "product_length_cm": "INTEGER", "product_height_cm": "INTEGER", "product_width_cm": "INTEGER"}),
    "sellers": ("olist_sellers_dataset.csv", {
        "seller_id": "VARCHAR", "seller_zip_code_prefix": "VARCHAR", "seller_city": "VARCHAR",
        "seller_state": "VARCHAR"}),
    "category_translation": ("product_category_name_translation.csv", {
        "product_category_name": "VARCHAR", "product_category_name_english": "VARCHAR"}),
}


def load(db_path=DB_PATH, raw_dir=RAW_DIR, quiet=False):
    missing = [f for f, _ in TABLES.values() if not (raw_dir / f).exists()]
    if missing:
        raise SystemExit(f"Missing files in {raw_dir}: {missing}. See data/README.md.")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    for table, (fname, cols) in TABLES.items():
        col_spec = "{" + ", ".join(f"'{c}': '{t}'" for c, t in cols.items()) + "}"
        con.execute(f"""
            CREATE OR REPLACE TABLE raw.{table} AS
            SELECT * FROM read_csv('{(raw_dir / fname).as_posix()}',
                header = true, columns = {col_spec}, quote = '"', escape = '"',
                timestampformat = '%Y-%m-%d %H:%M:%S', nullstr = '')""")
        n = con.execute(f"SELECT COUNT(*) FROM raw.{table}").fetchall()[0][0]
        if not quiet:
            print(f"raw.{table:22s} {n:>9,} rows")
    con.close()


if __name__ == "__main__":
    load()
