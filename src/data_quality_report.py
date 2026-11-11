"""Write reports/DATA_QUALITY.md from dbt's run_results.json (after `dbt build`).

Usage:  python -m src.data_quality_report
"""
import json
import re

from src.config import DBT_DIR, REPORTS_DIR

# what each data-quality check means and how the models handle it
EXPLAIN = {
    "dq_orders_without_items": ("Orders with no line items", "Mostly canceled/unavailable; contribute R$0 to revenue"),
    "dq_delivered_without_date": ("'delivered' orders with no delivery date", "Excluded from delivery analysis (`is_delivered` = false)"),
    "dq_canceled_with_delivery_date": ("Canceled orders that have a delivery date", "Status is trusted; treated as invalid orders"),
    "dq_payment_mismatch": ("Payments differ from items + freight by > R$1", "Revenue uses items + freight; payments kept separately"),
    "dq_orders_without_payment": ("Orders with no payment record", "Kept; payment fields are NULL"),
    "dq_duplicate_reviews": ("Orders with 2+ reviews", "Latest answered review kept (`stg_reviews`)"),
    "dq_missing_category": ("Products with no category", "Labelled 'unknown'"),
    "dq_untranslated_category": ("Categories missing from the translation file", "Portuguese name kept"),
    "dq_delivered_before_purchase": ("Delivered or approved before purchase", "None found"),
    "dq_shipped_before_approved": ("Handed to carrier before payment approval", "Kept; not used in any metric"),
}


def build():
    path = DBT_DIR / "target" / "run_results.json"
    if not path.exists():
        raise SystemExit("Run `dbt build --project-dir dbt --profiles-dir dbt` first.")
    res = json.loads(path.read_text())["results"]
    tests = [r for r in res if r["unique_id"].startswith("test.")]
    models = [r for r in res if r["unique_id"].startswith("model.")]
    status = lambda s: {"pass": "pass", "warn": "warn", "fail": "FAIL", "error": "ERROR"}.get(s, s)
    dq = [t for t in tests if t["unique_id"].split(".")[2].startswith("dq_")]
    other = [t for t in tests if t not in dq]
    L = ["# Data quality (auto-generated from dbt test results, do not edit)", "",
         f"dbt build: {len(models)} models, {len(tests)} tests: "
         f"{sum(t['status'] == 'pass' for t in tests)} pass, {sum(t['status'] == 'warn' for t in tests)} warn, "
         f"{sum(t['status'] in ('fail', 'error') for t in tests)} fail.", "",
         "## Known source issues (warning-level checks)", "",
         "These are real issues in the Olist data. The checks warn rather than fail, and each is handled in the models.", "",
         "| Check | Rows found | Handling |", "|---|---|---|"]
    for t in sorted(dq, key=lambda t: -(t.get("failures") or 0)):
        name = t["unique_id"].split(".")[2]
        what, how = EXPLAIN.get(name, (name, ""))
        L.append(f"| {what} (`{name}`) | {t.get('failures') or 0:,} | {how} |")
    L += ["", "## Integrity checks (must pass)", "",
          "Primary keys unique and not null, foreign keys resolve, accepted values, value ranges, and reconciliation "
          "between layers (no item lost between staging and marts; monthly GMV equals the order-level total).", "",
          "| Test | Status |", "|---|---|"]
    for t in sorted(other, key=lambda t: t["unique_id"]):
        L.append(f"| `{t['unique_id'].split('.')[2]}` | {status(t['status'])} |")
    (REPORTS_DIR / "DATA_QUALITY.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Written {REPORTS_DIR / 'DATA_QUALITY.md'}")


if __name__ == "__main__":
    build()
