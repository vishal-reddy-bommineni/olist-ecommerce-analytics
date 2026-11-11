"""Paths shared by every script."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "olist.duckdb"
MARTS_DIR = ROOT / "data" / "marts"          # Parquet exports used by the dashboard (committed)
DBT_DIR = ROOT / "dbt"
REPORTS_DIR = ROOT / "reports"
FIG_DIR = REPORTS_DIR / "figures"
POWERBI_DIR = ROOT / "powerbi"
