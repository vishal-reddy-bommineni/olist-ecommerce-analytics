"""Export the mart tables to Parquet (dashboard) and CSV (Power BI).

Usage:  python -m src.export_marts          # Parquet in data/marts (dashboard + Power BI)
        python -m src.export_marts --csv    # also CSVs in powerbi/data (large, not committed)
"""
import sys

import duckdb

from src.config import DB_PATH, MARTS_DIR, POWERBI_DIR

MARTS = ["fct_orders", "fct_order_items", "dim_customers", "dim_products", "dim_sellers", "dim_date",
         "mart_monthly_kpis", "mart_cohort_retention", "mart_category_performance", "mart_state_delivery",
         "seller_scorecard"]
# star schema for Power BI: facts + dimensions
POWERBI = ["fct_orders", "fct_order_items", "dim_customers", "dim_products", "dim_sellers", "dim_date", "seller_scorecard"]


def export(csv=False):
    MARTS_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH), read_only=True)
    for t in MARTS:
        con.execute(f"COPY marts.{t} TO '{(MARTS_DIR / (t + '.parquet')).as_posix()}' (FORMAT parquet, COMPRESSION zstd)")
    for t in POWERBI if csv else []:
        (POWERBI_DIR / "data").mkdir(parents=True, exist_ok=True)
        con.execute(f"COPY marts.{t} TO '{(POWERBI_DIR / 'data' / (t + '.csv')).as_posix()}' (HEADER, DELIMITER ',')")
    con.close()
    print(f"Exported {len(MARTS)} marts to {MARTS_DIR}" + (f" and {len(POWERBI)} CSVs to {POWERBI_DIR / 'data'}" if csv else ""))


if __name__ == "__main__":
    export(csv="--csv" in sys.argv)
