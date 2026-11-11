"""Unit tests for helper code (no data needed)."""
import duckdb
import numpy as np
import pandas as pd

from scripts.run_business_questions import parse, to_md
from src.config import ROOT


def test_business_questions_parse():
    blocks = parse((ROOT / "sql" / "business_questions.sql").read_text(encoding="utf-8"))
    assert len(blocks) >= 10
    names = [b[0] for b in blocks]
    assert len(names) == len(set(names))
    for name, q, sql in blocks:
        assert q, f"{name} has no question"
        assert sql.lower().lstrip().startswith(("select", "with")), name
        assert ";" not in sql


def test_business_questions_parse_inline():
    text = "-- name: a\n-- Q: First?\nselect 1;\n\n-- name: b\n-- Q: Second?\nwith x as (select 2) select * from x;\n"
    assert parse(text) == [("a", "First?", "select 1"), ("b", "Second?", "with x as (select 2) select * from x")]


def test_to_md_formats():
    md = to_md(pd.DataFrame({"n": [827.0], "share": [0.40071], "gmv": [1234.5], "x": [np.nan],
                             "d": [pd.Timestamp("2017-11-24")]}))
    assert "| 827 | 0.4007 | 1,234.50 | - | 2017-11-24 |" in md


def test_load_raw_keeps_zip_leading_zeros(tmp_path):
    """ZIP prefixes must stay text: '01310' must not become 1310."""
    from src import load_raw
    raw = tmp_path / "raw"
    raw.mkdir()
    headers = {
        "olist_orders_dataset.csv": "order_id,customer_id,order_status,order_purchase_timestamp,order_approved_at,order_delivered_carrier_date,order_delivered_customer_date,order_estimated_delivery_date\no1,c1,delivered,2017-01-01 10:00:00,,,,2017-01-10 00:00:00\n",
        "olist_customers_dataset.csv": "customer_id,customer_unique_id,customer_zip_code_prefix,customer_city,customer_state\nc1,u1,01310,sao paulo,SP\n",
        "olist_order_items_dataset.csv": "order_id,order_item_id,product_id,seller_id,shipping_limit_date,price,freight_value\no1,1,p1,s1,2017-01-03 00:00:00,10.50,2.00\n",
        "olist_order_payments_dataset.csv": "order_id,payment_sequential,payment_type,payment_installments,payment_value\no1,1,boleto,1,12.50\n",
        "olist_order_reviews_dataset.csv": 'review_id,order_id,review_score,review_comment_title,review_comment_message,review_creation_date,review_answer_timestamp\nr1,o1,5,,"bom, chegou",2017-01-11 00:00:00,2017-01-12 10:00:00\n',
        "olist_products_dataset.csv": "product_id,product_category_name,product_name_lenght,product_description_lenght,product_photos_qty,product_weight_g,product_length_cm,product_height_cm,product_width_cm\np1,,,,,,,,\n",
        "olist_sellers_dataset.csv": "seller_id,seller_zip_code_prefix,seller_city,seller_state\ns1,04001,sao paulo,SP\n",
        "product_category_name_translation.csv": "﻿product_category_name,product_category_name_english\nbeleza_saude,health_beauty\n",
    }
    for f, text in headers.items():
        (raw / f).write_text(text, encoding="utf-8")
    db = tmp_path / "t.duckdb"
    load_raw.load(db_path=db, raw_dir=raw, quiet=True)
    c = duckdb.connect(str(db), read_only=True)
    assert c.execute("select customer_zip_code_prefix from raw.customers").fetchall()[0][0] == "01310"
    assert c.execute("select review_comment_message from raw.order_reviews").fetchall()[0][0] == "bom, chegou"
    assert c.execute("select product_category_name from raw.category_translation").fetchall()[0][0] == "beleza_saude"
    assert float(c.execute("select price from raw.order_items").fetchall()[0][0]) == 10.5
    c.close()
