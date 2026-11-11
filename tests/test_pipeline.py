"""Tests on the built marts (Parquet) and helper code. Run after `python run_pipeline.py`."""
from pathlib import Path

import duckdb
import pytest

from src.config import MARTS_DIR, ROOT

pytestmark = pytest.mark.skipif(not (MARTS_DIR / "fct_orders.parquet").exists(), reason="run the pipeline first")


@pytest.fixture(scope="module")
def con():
    c = duckdb.connect()
    for f in MARTS_DIR.glob("*.parquet"):
        c.execute(f"CREATE VIEW {f.stem} AS SELECT * FROM read_parquet('{f.as_posix()}')")
    yield c
    c.close()


def one(con, sql):
    return con.execute(sql).fetchall()[0][0]


def test_one_row_per_order(con):
    assert one(con, "select count(*) - count(distinct order_id) from fct_orders") == 0


def test_every_order_has_a_customer(con):
    assert one(con, "select count(*) from fct_orders where customer_unique_id is null") == 0


def test_item_grain(con):
    assert one(con, "select count(*) - count(distinct order_item_key) from fct_order_items") == 0


def test_order_value_equals_items(con):
    """Order value in the fact table must equal the sum of its items + freight."""
    diff = one(con, """
        select max(abs(o.order_value - coalesce(i.v, 0))) from fct_orders o
        left join (select order_id, sum(price + freight_value) v from fct_order_items group by 1) i using (order_id)""")
    assert diff < 0.01


def test_late_only_for_delivered(con):
    assert one(con, "select count(*) from fct_orders where is_late is not null and not is_delivered") == 0


def test_canceled_orders_are_not_valid(con):
    assert one(con, "select count(*) from fct_orders where order_status in ('canceled','unavailable') and is_valid_order") == 0


def test_one_review_per_order(con):
    assert one(con, "select count(*) from fct_orders where review_score not between 1 and 5") == 0


def test_repeat_customer_means_a_later_day(con):
    assert one(con, "select count(*) from dim_customers where is_repeat_customer and purchase_days < 2") == 0
    assert one(con, "select count(*) from dim_customers where not is_repeat_customer and purchase_days > 1") == 0


def test_customer_orders_add_up(con):
    a = one(con, "select sum(orders) from dim_customers")
    b = one(con, "select count(*) from fct_orders where is_valid_order")
    assert a == b


def test_retention_rates_valid(con):
    assert one(con, "select count(*) from mart_cohort_retention where retention_rate not between 0 and 1") == 0
    # month 0 = the acquisition month itself, every cohort member is active
    assert one(con, "select min(retention_rate) from mart_cohort_retention where months_since_first = 0") == 1


def test_monthly_kpis_complete_months(con):
    months = [r[0] for r in con.execute("select strftime(order_month, '%Y-%m') from mart_monthly_kpis order by 1").fetchall()]
    assert months[0] == "2017-01" and months[-1] == "2018-08" and len(months) == 20


def test_monthly_gmv_reconciles(con):
    a = one(con, "select sum(gmv) from mart_monthly_kpis")
    b = one(con, """select round(sum(order_value), 2) from fct_orders
                    where is_valid_order and order_month between '2017-01-01' and '2018-08-01'""")
    assert abs(a - b) < 1


def test_category_shares_sum_to_one(con):
    assert abs(one(con, "select sum(revenue_share) from mart_category_performance") - 1) < 1e-3


def test_seller_scorecard_flags(con):
    assert one(con, "select count(*) from seller_scorecard where is_at_risk and not is_established") == 0
    assert one(con, "select count(*) - count(distinct revenue_rank) from seller_scorecard") == 0


def test_dim_date_is_continuous(con):
    days, span = con.execute("select count(*), date_diff('day', min(date), max(date)) + 1 from dim_date").fetchall()[0]
    assert days == span
